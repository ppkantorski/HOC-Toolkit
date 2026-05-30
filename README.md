# HOC Toolkit (Ultrahand 2.4.4+)

[![platform](https://img.shields.io/badge/platform-Switch-898c8c)](https://gbatemp.net/forums/nintendo-switch.283/?prefix_id=44)
[![language](https://img.shields.io/badge/language-UltraScript-ba1632.svg)](https://github.com/topics/ultrahand-package)
[![GPLv2 License](https://img.shields.io/badge/license-GPLv2-189c11.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Latest Version](https://img.shields.io/github/v/release/ppkantorski/HOC-Toolkit?label=latest&color=blue)](https://github.com/ppkantorski/HOC-Toolkit/releases/latest)
[![GitHub issues](https://img.shields.io/github/issues/ppkantorski/HOC-Toolkit?color=222222)](https://github.com/ppkantorski/HOC-Toolkit/issues)
[![GitHub stars](https://img.shields.io/github/stars/ppkantorski/HOC-Toolkit)](https://github.com/ppkantorski/HOC-Toolkit/stargazers)

**HOC Toolkit** is an [Ultrahand](https://github.com/ppkantorski/Ultrahand-Overlay) package for advanced overclocking configuration on the Nintendo Switch, built specifically for [Horizon OC](https://github.com/Horizon-OC/Horizon-OC). It provides a full in-overlay GUI for tuning RAM, CPU, GPU, and SoC parameters directly against the `hoc.kip` kernel patch (no PC required).

> **⚠️ Warning:** This package exposes low-level hardware parameters. Incorrect values can cause instability or crashes. Use with caution and proper guidance.

---

## Features

### RAM
- **Max Clock** — select RAM frequency (Mariko: single target; Erista: independent voltage targets for 665 / 800 / 1065 MHz)
- **Step Mode** — configure EMC step behavior
- **VDD2** — memory core voltage
- **VDDQ** *(Mariko only)* — memory I/O voltage
- **EMC DVB** — SoC EMC DVB shift configuration
- **HP Mode** — toggle high-performance EMC mode

### CPU
- **Low / High UV Mode** *(Mariko)* — independent named-step trackbar undervolting for low and high frequency ranges
- **CPU Table** *(Mariko)* — select CPU frequency/voltage curve table
- **UV Mode** *(Erista)* — select from predefined CPU undervolt profiles
- **Max Clock** *(Mariko)* — cap maximum CPU frequency
- **Boost Clock** *(Mariko / Erista)* — configure boost clock target
- **Low / High Freq Vmin** *(Mariko)* — minimum voltages for low and high frequency domains
- **Vmin** *(Erista)* — CPU minimum voltage
- **Voltage Limit** *(Mariko / Erista)* — cap maximum CPU voltage
- **CPU Unlock** *(Erista)* — unlock higher CPU frequency ranges

### GPU
- **GPU Table** *(Mariko / Erista)* — select GPU undervolt table profile
- **Vmin** *(Mariko / Erista)* — GPU minimum voltage
- **Vmax** *(Mariko only)* — GPU maximum voltage
- **Voltage Offset** — global GPU voltage offset
- **High UV Table** — per-frequency voltage assignment for every GPU clock step (Mariko: 76–1536 MHz; Erista: 76–1075 MHz)

### Timings
- **T1–T8** — individual DRAM timing parameters (tRCD, tRP, tRAS, tRRD/tFAW, tRFC, tRTW, tWTR, tREFI)
- **Timings TBreak** — max clock timing break with T2 RP Cap and fine-tune controls for T6 tRTW and T7 tWTR
- **Presets** — one-tap vendor timing profiles (Samsung, Hynix, Micron, Default)
- **Read / Write Latency** — per-platform latency tuning
- **Advanced Latency** *(Mariko)* — per-bucket read/write latency control across four latency regions (Latency 0–3)

### Tools
- **Info** — live dashboard showing current RAM, CPU, GPU, and SoC parameters read directly from `hoc.kip`
- **Backup System** — 21 named save/restore slots for full configuration snapshots; each slot displays a timing and voltage summary on load
- **AMS Settings** — toggle GPU Scheduling, Always Save Cheats, Controller Sync (BT DB), and Hold R for HB Menu directly from the overlay; includes Fan Curve optimizer
- **hekate Settings** — select the active bootloader INI, and patch or remove `hoc.kip` entries per boot entry or globally
- **Software Update** — one-tap update for HOC Toolkit, Horizon OC, sys-clk-hoc, sys-clk, Status Monitor, SaltyNX, Atmosphere, hekate, and Ultrahand Overlay
- **Reboot To** — reboot directly into any Hekate boot entry, Hekate menu, or UMS mode

### Fan Curve *(inside AMS Settings)*
- **Tskin Target** — step trackbar (52–60 °C) that optimizes the system fan curve for sustained higher clocks by writing a custom `tc` table to `system_settings.ini`

---

## Requirements

- Nintendo Switch (Erista or Mariko)
- [Atmosphere](https://github.com/Atmosphere-NX/Atmosphere) custom firmware
- [Ultrahand Overlay](https://github.com/ppkantorski/Ultrahand-Overlay) (latest)
- [Horizon OC](https://github.com/Horizon-OC/Horizon-OC) `hoc.kip` present at `/atmosphere/kips/hoc.kip`

---

## Installation

1. Download the latest release zip from the [Releases](https://github.com/Horizon-OC/HOC-Toolkit/releases/latest) page.
2. Extract to the root of your SD card. The package folder will be placed at:
   ```
   /switch/.packages/HOC Toolkit/
   ```
3. Boot into CFW and open Ultrahand Overlay (`ZL+ZR+DDOWN` by default).
4. Navigate to **Packages → HOC Toolkit**.

> The package reads and writes directly to `hoc.kip` at runtime. A reboot is required for changes to take effect.

---

## File Structure

```
sdmc:/
├── config/
│   └── ultrahand/
│       └── assets/
│           └── notifications/
│               └── hoc.rgba                 ← HOC notification icon (.rgba format)
└── switch/
    └── .packages/
        └── HOC Toolkit/
            ├── package.ini                  ← main menu (RAM / CPU / GPU / Tools)
            ├── boot_package.ini             ← syncs all footers on every overlay boot
            ├── exit_package.ini             ← cleanup on overlay exit
            ├── timings.ini                  ← timing submenu
            ├── advanced_ram_latency.ini     ← per-bucket latency editor (Mariko)
            ├── gpu_table_high_uv.ini        ← per-frequency GPU voltage table
            ├── software_update.ini          ← software update menu
            ├── global_cmds.ini              ← shared command macros
            ├── include/
            │   ├── backup/
            │   │   ├── backup.ini           ← backup slot UI
            │   │   ├── backup_info.ini      ← backup slot detail view
            │   │   └── backup_labels.txt
            │   ├── info/
            │   │   └── info.ini             ← live info dashboard
            │   ├── ram/
            │   │   ├── timing_presets.ini   ← vendor timing preset menu
            │   │   ├── preset_samsung.ini
            │   │   ├── preset_hynix.ini
            │   │   ├── preset_micron.ini
            │   │   └── preset_default.ini
            │   └── settings/
            │       ├── ams_settings.ini     ← AMS toggles + fan curve
            │       ├── fan_curve.ini        ← fan curve optimizer
            │       └── hekate_settings.ini  ← bootloader INI manager
            ├── erista/                      ← Erista-specific option JSON files
            ├── mariko/                      ← Mariko-specific option JSON files
            └── json/                        ← shared lookup and option JSON files
```

---

## How It Works

HOC Toolkit uses Ultrahand's `hex-by-custom-offset` command to read and write values directly into the `CUST` section of `hoc.kip`. Each setting maps to a specific byte offset within that section. The `boot_package.ini` runs automatically whenever Ultrahand opens and refreshes all displayed footer values to match what is currently in the KIP — keeping the UI in sync without a reboot.

Platform-specific sections are gated using Ultrahand's `erista:` and `mariko:` guards, so only the controls relevant to your console appear in the menu.

---

## Credits

HOC Toolkit is a continuation of the original [OC Toolkit](https://github.com/ppkantorski/Ultrahand-Overlay/tree/main/examples/OC%20Toolkit), which was further developed in [OC Switchcraft EOS](https://github.com/halop/OC-Switchcraft-EOS) by [halop](https://github.com/halop) and later with preliminary updates for HOC by [NaGaa95](https://github.com/NaGaa95).

| Contributor | Role |
|---|---|
| [ppkantorski](https://github.com/ppkantorski) | OC Toolkit development; OC Switchcraft EOS development |
| [halop (B3711)](https://github.com/halop) | OC Toolkit development; OC Switchcraft EOS development |
| [NaGaa95](https://github.com/NaGaa95) | EOS Pro development |

---

## Contributing

Contributions are welcome. Please open an [issue](https://github.com/Horizon-OC/HOC-Toolkit/issues/new) or submit a [pull request](https://github.com/Horizon-OC/HOC-Toolkit/compare).

---

## License

Licensed and distributed under [GPLv2](LICENSE).

Copyright © 2023–2026 ppkantorski
