# HOC Toolkit

[![platform](https://img.shields.io/badge/platform-Switch-898c8c)](https://gbatemp.net/forums/nintendo-switch.283/?prefix_id=44)
[![language](https://img.shields.io/badge/language-UltraScript-ba1632.svg)](https://github.com/topics/ultrahand-package)
[![GPLv2 License](https://img.shields.io/badge/license-GPLv2-189c11.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Latest Version](https://img.shields.io/github/v/release/ppkantorski/HOC-Toolkit?label=latest&color=blue)](https://github.com/ppkantorski/HOC-Toolkit/releases/latest)
[![GitHub issues](https://img.shields.io/github/issues/ppkantorski/HOC-Toolkit?color=222222)](https://github.com/ppkantorski/HOC-Toolkit/issues)
[![GitHub stars](https://img.shields.io/github/stars/ppkantorski/HOC-Toolkit)](https://github.com/ppkantorski/HOC-Toolkit/stargazers)

**HOC Toolkit** is an [Ultrahand](https://github.com/ppkantorski/Ultrahand-Overlay) package for advanced overclocking configuration on the Nintendo Switch, built specifically for [Horizon OC](https://github.com/Horizon-OC/Horizon-OC) (HOC 2.1.0). It provides a full in-overlay GUI for tuning RAM, CPU, GPU, and SoC parameters directly against the `hoc.kip` kernel patch — no PC required.

> **⚠️ Warning:** This package exposes low-level hardware parameters. Incorrect values can cause instability or crashes. Use with caution and proper guidance.

---

## Features

### RAM
- **Max Clock** — select RAM frequency (Mariko: single target; Erista: per-frequency voltage control for 665 / 800 / 1065 MHz)
- **RAM Frequency Editor** *(Erista only)* — fine-grained per-frequency voltage tuning
- **Step Mode** — configure EMC step behavior
- **Vdd2** — memory core voltage
- **Vddq** *(Mariko only)* — memory I/O voltage
- **HP Mode** — toggle high-performance EMC mode

### CPU
- **Undervolt Mode** *(Erista)* — select from predefined CPU undervolt profiles
- **Low / High UV Mode** *(Mariko)* — independent named-step trackbar undervolting for low and high frequency ranges
- **CPU Table** *(Mariko)* — select CPU frequency/voltage curve table
- **Max Clock** *(Mariko)* — cap maximum CPU frequency
- **Boost Clock** *(Mariko / Erista)* — configure boost clock target
- **Low / High Freq Vmin** *(Mariko)* — minimum voltages for low and high frequency domains
- **Vmin** *(Erista)* — CPU minimum voltage
- **Voltage Limit** *(Mariko / Erista)* — cap maximum CPU voltage
- **CPU Unlock** *(Erista)* — unlock higher CPU frequency ranges

### GPU
- **Undervolt Mode** *(Mariko / Erista)* — select GPU undervolt table profile
- **Vmin** *(Mariko / Erista)* — GPU minimum voltage
- **Vmax** *(Mariko only)* — GPU maximum voltage
- **Voltage Offset** — global GPU voltage offset
- **Custom Table** — per-frequency voltage assignment for every GPU clock step (Mariko: 76–1536 MHz; Erista: 76–1075 MHz)

### Timings
- **Presets** — one-tap vendor timing profiles (Samsung, Hynix, Micron, Default)
- **Read / Write Latency** — per-platform latency tuning
- **Advanced Latency** *(Mariko)* — per-bucket read/write latency control across all four latency regions
- **T1–T8** — individual DRAM timing parameters (tRCD, tRP, tRAS, tRRD/tFAW, tRFC, tRTW, tWTR, tREFI)

### SoC
- **Voltage Shift** — SoC DVB shift configuration

### Tools
- **Info** — live dashboard showing current RAM, CPU, GPU, and SoC parameters read directly from `hoc.kip`
- **Backup System** — named save/restore slots for full configuration snapshots; each slot stores all tunable values and displays a timing summary on load
- **System Settings** — toggle GPU Scheduling, Always Save Cheats, Controller Sync (BT DB), and Hold R for HB Menu directly from the overlay
- **Fan Curve** — optimize the system fan curve for higher clocks, with a Tskin target step trackbar (52–60 °C)
- **Reboot To** — reboot directly into any Hekate boot entry, Hekate menu, or UMS mode

---

## Requirements

- Nintendo Switch (Erista or Mariko)
- [Atmosphere](https://github.com/Atmosphere-NX/Atmosphere) custom firmware
- [Ultrahand Overlay](https://github.com/ppkantorski/Ultrahand-Overlay) (latest)
- [Horizon OC](https://github.com/Horizon-OC/Horizon-OC) 2.1.0+ with `hoc.kip` present at `/atmosphere/kips/hoc.kip`

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
SD Card Root
└── switch/
    └── .packages/
        └── HOC Toolkit/
            ├── package.ini             ← main menu (RAM / CPU / GPU / SoC)
            ├── boot_package.ini        ← syncs all footers on every overlay boot
            ├── timings.ini             ← timing submenu
            ├── timing_presets.ini      ← vendor timing presets
            ├── advanced_ram_latency.ini← per-bucket latency editor (Mariko)
            ├── backup.ini              ← backup slot UI
            ├── backup_info.ini         ← backup slot detail view
            ├── backup_labels.txt
            ├── custom_table.ini        ← per-frequency GPU voltage table
            ├── fan_curve.ini           ← fan curve optimizer
            ├── info.ini                ← live info dashboard
            ├── system-settings.ini     ← system toggle menu
            ├── ram_erista.ini          ← Erista per-frequency RAM voltage editor
            ├── ram_volt.ini
            ├── preset_*.ini            ← vendor timing preset definitions
            ├── config.ini              ← runtime footer state (auto-managed)
            ├── erista/                 ← Erista-specific option JSON files
            ├── mariko/                 ← Mariko-specific option JSON files
            └── json/                   ← shared lookup and option JSON files
```

---

## How It Works

HOC Toolkit uses Ultrahand's `hex-by-custom-offset` command to read and write values directly into the `CUST` section of `hoc.kip`. Each setting maps to a specific byte offset within that section. The `boot_package.ini` runs automatically whenever Ultrahand opens and refreshes all displayed footer values to match what is currently in the KIP — keeping the UI in sync without a reboot.

Platform-specific sections are gated using Ultrahand's `erista:` and `mariko:` guards, so only the controls relevant to your console appear in the menu.

---

## Credits

HOC Toolkit is a continuation of the original [OC Toolkit](https://github.com/ppkantorski/Ultrahand-Overlay/tree/main/examples/OC%20Toolkit) by [ppkantorski](https://github.com/ppkantorski), which was further developed in [OC Switchcraft EOS](https://github.com/halop/OC-Switchcraft-EOS) by [halop](https://github.com/halop) and later with preliminary updates for HOC by [NaGaa95](https://github.com/NaGaa95).

| Contributor | Role |
|---|---|
| [ppkantorski](https://github.com/ppkantorski) | Original OC Toolkit author; Ultrahand Overlay |
| [B3711](https://github.com/B3711) | HOC Toolkit development |
| [NaGa](https://github.com/NaGa) | HOC Toolkit development |
| [MestreYodaRossi](https://github.com/MestreYodaRossi) | HOC Toolkit development |

---

## Contributing

Contributions are welcome. Please open an [issue](https://github.com/Horizon-OC/HOC-Toolkit/issues/new) or submit a [pull request](https://github.com/Horizon-OC/HOC-Toolkit/compare).

---

## License

Licensed and distributed under [GPLv2](LICENSE).
Copyright © 2023–2026 ppkantorski
