#!/usr/bin/env python3
"""
patch_ini.py — HOC Toolkit INI Patcher
=======================================
Reads your desired CUST values from cust_master_list.json and bakes them
directly into every hex-by-custom-offset command inside the HOC Toolkit
INI files, replacing dynamic Ultrahand expressions like:

    {json_file_source(*,hex)}
    {ini_file(Backup,someKey)}

with the static little-endian hex bytes for the corresponding field.

Lines that already carry a static 8-character hex argument (e.g. the
on/off toggle commands `01000000` / `00000000`, or preset entries) are
left completely untouched — only dynamic `{...}` arguments are replaced.

Usage
-----
  python patch_ini.py [--toolkit <dir>] [--json <path>] [--no-backup] [--dry-run] [--restore]

  --toolkit   Path to the "HOC Toolkit" folder   (default: ./HOC Toolkit)
  --json      Path to cust_master_list.json       (default: ./cust_master_list.json)
  --no-backup Skip creating .bak copies of each patched INI file
  --dry-run   Show what would change without writing anything
  --restore   Restore every .bak file back to the original (undo all patches)

What counts as a patchable line
--------------------------------
Any line matching:

    hex-by-custom-offset /atmosphere/kips/hoc.kip CUST <offset> {<expr>}

where the 4th token starts with `{`. Static-hex lines are skipped.

Value encoding
--------------
Each field value from the JSON is packed as a 4-byte unsigned little-endian
integer and formatted as exactly 8 lowercase hex characters — the same format
Ultrahand expects, e.g. value 1175000 → 58e61100.
"""

import argparse
import glob
import json
import os
import re
import shutil
import struct
import sys

# ── Pattern ────────────────────────────────────────────────────────────────────
# Matches:  hex-by-custom-offset /atmosphere/kips/hoc.kip CUST <offset> <payload>
# Group 1 = everything up to and including the offset + space
# Group 2 = the numeric offset
# Group 3 = the payload  (static hex OR dynamic {expr})
# Group 4 = trailing whitespace / line-ending
HEX_CMD_RE = re.compile(
    r"(hex-by-custom-offset\s+/atmosphere/kips/hoc\.kip\s+CUST\s+(\d+)\s+)"
    r"(\S+)"
    r"([ \t]*\r?\n?)"
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def pack_le_hex(value: int) -> str:
    """Return value as 8-char lowercase little-endian hex string."""
    return struct.pack("<I", value).hex()


def build_offset_map(master: dict) -> dict[int, tuple[str, int]]:
    """
    Walk the master JSON and return  { offset: (field_name, value) }.
    Only includes fields with an 'offset' key and not marked read_only.
    """
    result = {}
    for section_key, section_val in master.items():
        if section_key.startswith("_"):
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
            if field_data.get("read_only"):
                continue
            if field_name in ("cust_magic", "custRev", "placeholder"):
                continue
            offset = int(field_data["offset"])
            value  = int(field_data["value"])
            result[offset] = (field_name, value)
    return result


def is_dynamic(payload: str) -> bool:
    """Return True if the payload is a dynamic Ultrahand expression {…}."""
    return payload.startswith("{")


def patch_content(content: str, offset_map: dict, ini_path: str, dry_run: bool) -> tuple[str, list[str]]:
    """
    Process the full text of one INI file.
    Returns (new_content, list_of_change_descriptions).
    """
    changes = []
    out_parts = []
    pos = 0

    for m in HEX_CMD_RE.finditer(content):
        prefix   = m.group(1)
        offset   = int(m.group(2))
        payload  = m.group(3)
        trailing = m.group(4)

        # Copy the literal text before this match
        out_parts.append(content[pos:m.start()])
        pos = m.end()

        if not is_dynamic(payload):
            # Static hex — leave exactly as-is
            out_parts.append(m.group(0))
            continue

        if offset not in offset_map:
            # Dynamic but we have no mapping — warn and leave as-is
            rel = os.path.relpath(ini_path)
            changes.append(
                f"  WARN  {rel}  offset {offset}  — no JSON field, left as {payload}"
            )
            out_parts.append(m.group(0))
            continue

        field_name, value = offset_map[offset]
        new_hex = pack_le_hex(value)

        if payload != new_hex:  # it's {expr}, not matching yet — always different
            changes.append(
                f"  PATCH {os.path.relpath(ini_path):<45}  "
                f"CUST {offset:>3}  ({field_name})  {payload} → {new_hex}"
            )

        # Reconstruct the line with the static hex
        out_parts.append(prefix + new_hex + trailing)

    # Append remainder after last match
    out_parts.append(content[pos:])
    return "".join(out_parts), changes


# ── Restore mode ──────────────────────────────────────────────────────────────

def restore_backups(toolkit_dir: str) -> None:
    bak_files = glob.glob(os.path.join(toolkit_dir, "*.ini.bak"))
    if not bak_files:
        print("  No .bak files found — nothing to restore.")
        return
    for bak in sorted(bak_files):
        original = bak[:-4]  # strip .bak
        shutil.copy2(bak, original)
        os.remove(bak)
        print(f"  Restored  {os.path.relpath(original)}")
    print(f"\n  {len(bak_files)} file(s) restored.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bake CUST values from cust_master_list.json into HOC Toolkit INI files."
    )
    parser.add_argument("--toolkit",   default="HOC Toolkit",         help='Path to "HOC Toolkit" folder')
    parser.add_argument("--json",      default="cust_master_list.json", help="Path to cust_master_list.json")
    parser.add_argument("--no-backup", action="store_true",            help="Skip .bak backups")
    parser.add_argument("--dry-run",   action="store_true",            help="Print changes without writing")
    parser.add_argument("--restore",   action="store_true",            help="Restore from .bak files")
    args = parser.parse_args()

    print(f"\n{'='*65}")
    print(f"  HOC Toolkit INI Patcher")
    print(f"  Toolkit : {os.path.abspath(args.toolkit)}")
    print(f"  JSON    : {os.path.abspath(args.json)}")
    print(f"{'='*65}\n")

    # ── Restore mode ──
    if args.restore:
        restore_backups(args.toolkit)
        print()
        return

    # ── Validate inputs ──
    if not os.path.isdir(args.toolkit):
        print(f"ERROR: Toolkit folder not found: {args.toolkit}")
        sys.exit(1)
    if not os.path.isfile(args.json):
        print(f"ERROR: JSON not found: {args.json}")
        sys.exit(1)

    with open(args.json, "r", encoding="utf-8") as f:
        master = json.load(f)

    offset_map = build_offset_map(master)
    print(f"  Loaded {len(offset_map)} patchable field(s) from JSON.\n")

    # ── Find INI files ──
    ini_files = sorted(glob.glob(os.path.join(args.toolkit, "*.ini")))
    if not ini_files:
        print("ERROR: No .ini files found in toolkit folder.")
        sys.exit(1)

    total_patches = 0
    total_warnings = 0
    patched_files = 0

    for ini_path in ini_files:
        with open(ini_path, "r", encoding="utf-8", errors="replace") as f:
            original = f.read()

        new_content, changes = patch_content(original, offset_map, ini_path, args.dry_run)

        patch_changes  = [c for c in changes if c.startswith("  PATCH")]
        warn_changes   = [c for c in changes if c.startswith("  WARN")]

        total_patches  += len(patch_changes)
        total_warnings += len(warn_changes)

        if not changes:
            continue  # Nothing to do for this file

        patched_files += 1
        print(f"  ── {os.path.relpath(ini_path)} ──")
        for c in changes:
            print(c)

        if not args.dry_run and patch_changes:
            if not args.no_backup:
                bak = ini_path + ".bak"
                shutil.copy2(ini_path, bak)

            # Preserve original line endings per-file
            # (detect from first \r\n vs \n in original)
            if "\r\n" in original and "\r\n" not in new_content:
                new_content = new_content.replace("\n", "\r\n")

            with open(ini_path, "w", encoding="utf-8", newline="") as f:
                f.write(new_content)
        print()

    # ── Summary ──
    print("─" * 65)
    if args.dry_run:
        print(f"  [DRY RUN] Would patch {total_patches} line(s) across {patched_files} file(s).")
    else:
        print(f"  Patched {total_patches} line(s) across {patched_files} file(s).")
        if not args.no_backup and patched_files > 0:
            print(f"  Backups saved as <filename>.ini.bak  (undo: --restore)")
    if total_warnings:
        print(f"  {total_warnings} warning(s): dynamic lines with no JSON mapping were skipped.")
    print()


if __name__ == "__main__":
    main()
