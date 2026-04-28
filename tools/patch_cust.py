#!/usr/bin/env python3
"""
patch_cust.py — HOC CUST Table Patcher for hoc.kip
====================================================
Reads every writable field from cust_master_list.json and patches the
corresponding bytes inside hoc.kip at the correct offset from the CUST
magic signature.

Usage
-----
  python patch_cust.py [--kip <path>] [--json <path>] [--no-backup] [--dry-run] [--read]

  --kip       Path to hoc.kip            (default: ./hoc.kip)
  --json      Path to cust_master_list.json (default: ./cust_master_list.json)
  --no-backup Skip creating a .bak backup before patching
  --dry-run   Print what would be patched without writing anything
  --read      Dump the current CUST values from the kip without patching

How it works
------------
Ultrahand's hex-by-custom-offset command:
  hex-by-custom-offset <file> CUST <offset> <little-endian hex bytes>

searches for the 4-byte magic 0x43555354 ("CUST") in the binary, then
writes <size> bytes at <offset> bytes past the START of that magic.

This script mirrors that behaviour exactly:
  1. Find the CUST magic in the kip.
  2. For each non-read-only field in the JSON, pack value as u32 LE.
  3. Write 4 bytes at (cust_pos + field["offset"]).

Safety checks performed before any write:
  - CUST magic is present and unique in the file.
  - custRev at offset 4 matches the expected value (2).
  - Field offset + 4 does not exceed file size.
  - For fields with allowed_values, the value is in that list.
  - File is writeable (unless --dry-run).
"""

import argparse
import json
import os
import shutil
import struct
import sys

# ── Constants ────────────────────────────────────────────────────────────────

CUST_MAGIC       = b"CUST"             # 0x43555354
CUST_REV_OFFSET  = 4                   # u32 at offset 4 from magic
EXPECTED_CUST_REV = 2

# Fields in the JSON that should never be written to the binary
READ_ONLY_FIELDS  = {"cust_magic", "custRev", "placeholder"}

# JSON section keys that are just metadata
META_KEYS         = {"_description", "_meta", "_note"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def pack_u32(value: int) -> bytes:
    """Pack an integer as a 4-byte little-endian uint32."""
    return struct.pack("<I", value)


def unpack_u32(data: bytes, offset: int) -> int:
    """Read a 4-byte little-endian uint32 from data at offset."""
    return struct.unpack_from("<I", data, offset)[0]


def find_cust_offset(data: bytes) -> int:
    """
    Find the byte position of the CUST magic in the binary.
    Raises ValueError if not found or if multiple occurrences exist.
    """
    positions = []
    start = 0
    while True:
        pos = data.find(CUST_MAGIC, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1

    if not positions:
        raise ValueError(
            "CUST magic (0x43555354) not found in the kip file.\n"
            "Make sure this is a valid hoc.kip with an embedded CUST table."
        )
    if len(positions) > 1:
        raise ValueError(
            f"CUST magic found at multiple offsets: {[hex(p) for p in positions]}.\n"
            "Cannot safely determine the correct CUST table. Aborting."
        )
    return positions[0]


def collect_fields(master: dict) -> list[dict]:
    """
    Walk every section of the master JSON and collect patchable field entries.
    Returns a list of dicts, each with at least: name, offset, size, value,
    read_only, section.
    """
    fields = []
    for section_key, section_val in master.items():
        if section_key.startswith("_") or section_key == "_meta":
            continue
        if not isinstance(section_val, dict):
            continue
        for field_name, field_data in section_val.items():
            if field_name.startswith("_"):
                continue
            if not isinstance(field_data, dict):
                continue
            if "offset" not in field_data:
                continue
            entry = dict(field_data)
            entry["name"]    = field_name
            entry["section"] = section_key
            entry.setdefault("read_only", field_name in READ_ONLY_FIELDS)
            entry.setdefault("size", 4)
            fields.append(entry)
    return fields


def validate_field(field: dict, cust_data_len: int) -> None:
    """
    Run safety checks on a single field before writing.
    Raises ValueError with a descriptive message if anything is wrong.
    """
    name      = field["name"]
    offset    = field["offset"]
    size      = field["size"]
    value     = field["value"]
    field_end = offset + size

    if field_end > cust_data_len:
        raise ValueError(
            f"Field '{name}': offset {offset} + size {size} = {field_end} "
            f"exceeds available data length {cust_data_len}."
        )

    # u32 range check (unsigned)
    if not (0 <= value <= 0xFFFFFFFF):
        raise ValueError(
            f"Field '{name}': value {value} is outside u32 range [0, 4294967295]."
        )

    # allowed_values check
    if "allowed_values" in field and value not in field["allowed_values"]:
        raise ValueError(
            f"Field '{name}': value {value} is not in allowed_values "
            f"{field['allowed_values']}."
        )


# ── Main logic ────────────────────────────────────────────────────────────────

def read_mode(kip_path: str, master: dict) -> None:
    """Dump the current CUST field values from the kip without patching."""
    with open(kip_path, "rb") as f:
        data = bytearray(f.read())

    cust_pos = find_cust_offset(data)
    print(f"  CUST magic found at file offset: 0x{cust_pos:08X} ({cust_pos})")

    # Verify custRev
    rev = unpack_u32(data, cust_pos + CUST_REV_OFFSET)
    print(f"  custRev = {rev} (expected {EXPECTED_CUST_REV})")
    if rev != EXPECTED_CUST_REV:
        print(f"  WARNING: custRev mismatch — file has {rev}, expected {EXPECTED_CUST_REV}.")

    fields = collect_fields(master)
    fields.sort(key=lambda f: f["offset"])

    print(f"\n{'Section':<25} {'Field':<35} {'Offset':>7} {'Current Value':>15}")
    print("-" * 88)
    for field in fields:
        if field.get("read_only") and field["name"] not in ("custRev",):
            continue
        abs_offset = cust_pos + field["offset"]
        if abs_offset + 4 > len(data):
            print(f"  WARNING: {field['name']} at offset {field['offset']} out of bounds")
            continue
        current = unpack_u32(data, abs_offset)
        flag = " [READ-ONLY]" if field.get("read_only") else ""
        print(f"  {field['section']:<23} {field['name']:<35} {field['offset']:>7}   {current:>13}{flag}")


def patch_mode(kip_path: str, master: dict, backup: bool, dry_run: bool) -> None:
    """Read values from the JSON and patch the kip binary."""
    with open(kip_path, "rb") as f:
        data = bytearray(f.read())

    cust_pos = find_cust_offset(data)
    print(f"  CUST magic at file offset: 0x{cust_pos:08X} ({cust_pos})")

    # Verify custRev
    rev = unpack_u32(data, cust_pos + CUST_REV_OFFSET)
    if rev != EXPECTED_CUST_REV:
        print(
            f"\n  ERROR: custRev mismatch.\n"
            f"  The kip reports custRev={rev} but this script expects {EXPECTED_CUST_REV}.\n"
            f"  Aborting to prevent corrupt patches. Check your HOC version."
        )
        sys.exit(1)
    print(f"  custRev = {rev} ✓")

    # How many bytes are available from CUST to EOF
    available = len(data) - cust_pos

    fields = collect_fields(master)
    fields.sort(key=lambda f: f["offset"])

    # Separate patchable fields from read-only
    patchable = [f for f in fields if not f.get("read_only")]

    # Validate ALL fields before touching the file
    errors = []
    for field in patchable:
        try:
            validate_field(field, available)
        except ValueError as e:
            errors.append(str(e))
    if errors:
        print("\n  VALIDATION ERRORS — no bytes written:")
        for err in errors:
            print(f"    • {err}")
        sys.exit(1)

    # Backup
    if backup and not dry_run:
        bak_path = kip_path + ".bak"
        shutil.copy2(kip_path, bak_path)
        print(f"  Backup written → {bak_path}")

    # Patch
    changed = 0
    skipped = 0
    print(f"\n  {'Section':<25} {'Field':<35} {'Offset':>7}   {'Old':>10} → {'New':<10}")
    print("  " + "-" * 90)

    for field in patchable:
        abs_offset = cust_pos + field["offset"]
        old_val    = unpack_u32(data, abs_offset)
        new_val    = int(field["value"])

        if old_val == new_val:
            skipped += 1
            continue

        note = f"  {field['section']:<25} {field['name']:<35} {field['offset']:>7}   {old_val:>10} → {new_val:<10}"
        print(note)

        if not dry_run:
            new_bytes = pack_u32(new_val)
            data[abs_offset : abs_offset + 4] = new_bytes
        changed += 1

    # Write
    if not dry_run and changed > 0:
        with open(kip_path, "wb") as f:
            f.write(data)
        print(f"\n  Wrote {changed} field(s). {skipped} already matched.")
    elif dry_run:
        print(f"\n  [DRY RUN] Would patch {changed} field(s). {skipped} already matched. File not modified.")
    else:
        print(f"\n  All {skipped} field(s) already match. Nothing to do.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Patch HOC CUST table in hoc.kip from cust_master_list.json"
    )
    parser.add_argument("--kip",       default="hoc.kip",              help="Path to hoc.kip")
    parser.add_argument("--json",      default="cust_master_list.json", help="Path to cust_master_list.json")
    parser.add_argument("--no-backup", action="store_true",             help="Skip .bak backup")
    parser.add_argument("--dry-run",   action="store_true",             help="Print changes without writing")
    parser.add_argument("--read",      action="store_true",             help="Read and dump current CUST values")
    args = parser.parse_args()

    # ── Load JSON ──
    if not os.path.isfile(args.json):
        print(f"ERROR: JSON file not found: {args.json}")
        sys.exit(1)
    with open(args.json, "r", encoding="utf-8") as f:
        master = json.load(f)

    # ── Load KIP ──
    if not os.path.isfile(args.kip):
        print(f"ERROR: KIP file not found: {args.kip}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  HOC CUST Patcher")
    print(f"  KIP  : {os.path.abspath(args.kip)}")
    print(f"  JSON : {os.path.abspath(args.json)}")
    print(f"{'='*60}\n")

    if args.read:
        read_mode(args.kip, master)
    else:
        patch_mode(
            kip_path=args.kip,
            master=master,
            backup=not args.no_backup,
            dry_run=args.dry_run,
        )

    print()


if __name__ == "__main__":
    main()
