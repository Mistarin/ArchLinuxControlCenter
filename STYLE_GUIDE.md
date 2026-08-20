# CachyOS Control Center — Semantic Design & Style Guide

## Semantic Token Architecture

The UI and terminal renderers do not use hard-coded colors for action meanings (e.g. avoiding hardcoded green=install or blue=info). Instead, all styling is driven by **Semantic Tokens**:

| Token | Semantic Purpose |
|---|---|
| `--background` | Main application and page canvas background |
| `--surface` | Sidebar, header bars, and baseline containers |
| `--surface-2` | Elevated sharp cards, modals, tables, and nested cards |
| `--border` | Structural borders and dividers |
| `--text` | Primary high-contrast readable typography |
| `--muted` | Secondary text, captions, and metadata |
| `--accent` | Primary positive constructive actions (Install, Apply, Upgrade) |
| `--accent-2` | Informational highlights, secondary tools, and neutral actions |
| `--destructive` | **Shared across ALL themes (`#FF4D5A`)**: Warnings, delete, cache wipe, kill process, failures |
| `--warning` | Amber/orange status alerts and notices |
| `--success` | Green indicators and completion status |
| `--secondary-accent` | Branding and decorative highlights (e.g. dividing lines, neon tags) |

---

## Shared Destructive Red Rule
> **Rule:** `#FF4D5A` is strictly reserved for destructive operations, errors, and removal actions across **every** theme without exception. Non-destructive actions (like `Install`, `Upgrade`, `Apply`) must never use red.

---

## Theme Palettes

### 1. Minimalist White (Default)
Clean, technical, high-contrast light theme with drop shadows and distinct canvas separation.

| Token | Hex |
|---|---|
| **Background** | `#F4F5F7` |
| **Surface** | `#FFFFFF` |
| **Surface 2 (Cards)** | `#FFFFFF` |
| **Border** | `#E4E4E7` |
| **Text** | `#111111` |
| **Muted** | `#52525B` |
| **Accent / Install** | `#111111` |
| **Accent 2 / Info** | `#0284C7` |
| **Destructive** | `#FF4D5A` |
| **Warning** | `#D97706` |
| **Success** | `#059669` |
| **Secondary Accent** | `#EA580C` |

---

### 2. Dark — Neutral Graphite
Clean, technical, unobtrusive dark theme.

| Token | Hex |
|---|---|
| **Background** | `#0D0F12` |
| **Surface** | `#15181C` |
| **Surface 2 (Cards)** | `#1C2025` |
| **Border** | `#2A2F36` |
| **Text** | `#F1F3F5` |
| **Muted** | `#9AA1AA` |
| **Accent / Install** | `#7CFF8A` |
| **Accent 2 / Info** | `#6EA8FF` |
| **Destructive** | `#FF4D5A` |
| **Warning** | `#FFB454` |
| **Success** | `#54E38E` |
| **Secondary Accent** | `#6EA8FF` |

---

### 3. Dark Blue — Deep Navy
Deep navy with tinted surfaces for distinct visual depth while maintaining maximum contrast.

| Token | Hex |
|---|---|
| **Background** | `#080D16` |
| **Surface** | `#0E1624` |
| **Surface 2 (Cards)** | `#152033` |
| **Border** | `#26354A` |
| **Text** | `#E8F0FA` |
| **Muted** | `#8998AC` |
| **Accent / Install** | `#61E7A5` |
| **Accent 2 / Info** | `#5AA9FF` |
| **Destructive** | `#FF4D5A` |
| **Warning** | `#FFC15C` |
| **Success** | `#45D98A` |
| **Secondary Accent** | `#5AA9FF` |

---

### 4. Cyberpunk — Black / Violet / Neon
High-voltage aesthetic with neon green actions, cyan informational highlights, and magenta branding accents.

| Token | Hex |
|---|---|
| **Background** | `#09070D` |
| **Surface** | `#120D19` |
| **Surface 2 (Cards)** | `#1B1226` |
| **Border** | `#38234A` |
| **Text** | `#F5EEFF` |
| **Muted** | `#A895B8` |
| **Accent / Install** | `#00F5A0` |
| **Accent 2 / Info** | `#00D9FF` |
| **Destructive** | `#FF4D5A` |
| **Warning** | `#FFE14A` |
| **Success** | `#00F5A0` |
| **Secondary Accent (Decorative)** | `#D946EF` |

---

### 5. DOOM — Hellish Industrial
Industrial game-terminal aesthetic with amber install actions, cyan information, crimson decorative lines, and `#FF4D5A` destructive triggers.

| Token | Hex |
|---|---|
| **Background** | `#0C0908` |
| **Surface** | `#17110F` |
| **Surface 2 (Cards)** | `#211714` |
| **Border** | `#3A2821` |
| **Text** | `#F2E9E3` |
| **Muted** | `#A99A92` |
| **Accent / Install** | `#FFB52E` |
| **Accent 2 / Info** | `#5CC8FF` |
| **Destructive** | `#FF4D5A` |
| **Warning** | `#FF7A24` |
| **Success** | `#8EDC52` |
| **Secondary Accent (Decorative)** | `#C52A24` |

---

## Terminal Palette Mapping

Terminal outputs map directly to semantic tokens for high legibility on dark console backgrounds:

| Terminal Role | Dark | Dark Blue | Cyberpunk | DOOM |
|---|---|---|---|---|
| **Background** | `#0D0F12` | `#080D16` | `#09070D` | `#0C0908` |
| **Foreground / Text** | `#F1F3F5` | `#E8F0FA` | `#F5EEFF` | `#F2E9E3` |
| **Muted** | `#9AA1AA` | `#8998AC` | `#A895B8` | `#A99A92` |
| **Install / Action** | `#7CFF8A` | `#61E7A5` | `#00F5A0` | `#FFB52E` |
| **Info** | `#6EA8FF` | `#5AA9FF` | `#00D9FF` | `#5CC8FF` |
| **Warning** | `#FFB454` | `#FFC15C` | `#FFE14A` | `#FF7A24` |
| **Destructive / Error** | `#FF4D5A` | `#FF4D5A` | `#FF4D5A` | `#FF4D5A` |
| **Success** | `#54E38E` | `#45D98A` | `#00F5A0` | `#8EDC52` |
