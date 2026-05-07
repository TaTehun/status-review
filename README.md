# Tender Status Review — Automation Pipeline

An end-to-end Python automation pipeline that logs into a TMS web portal, queries today's tender requests by region, exports the results to Excel, and distributes a formatted report via email — with no manual steps.

> **Visual overview:** [project-overview.html](project-overview.html)

---

## Overview

Each business day, load planners need to review the current tender status for specific carriers across multiple regions. This pipeline runs three times per day (once per region), each triggered by Task Scheduler via a dedicated `.bat` file:

1. **Logs in** to the TMS portal via Selenium browser automation
2. **Searches** for today's tender requests filtered by carrier, status, and logistics group
3. **Customizes** the result columns to only include relevant fields
4. **Exports** the result set as an Excel file
5. **Formats** the file (column auto-fit, filters) and **sends** it via email with an embedded HTML summary table
6. **Alerts** on failure — a separate email is sent to a different recipient list if the export fails

---

## Project Structure

```
tender-status-review/
├── main.py                      # Full automation pipeline entry point
├── main_example.py              # Portfolio version (no sensitive values)
├── email_pipeline_example.py    # Portfolio version of the email pipeline
├── run_east_coast.bat           # Task Scheduler trigger — East region
├── run_central.bat              # Task Scheduler trigger — Central region
├── run_west_coast.bat           # Task Scheduler trigger — West region
├── email_pipeline/
│   ├── email_setup.py           # All settings (paths, SMTP, recipients, subjects)
│   └── sender.py                # EmailSender class + load_sender() factory
├── config_example.py            # Portfolio version of email_setup.py
├── utils/
│   ├── date_utils.py            # Date formatting utilities
│   └── email_utils.py           # xlsx formatting + HTML email body builder
└── brd/                         # Business requirement documents
```

---

## How It Works

### 1. Run Selection
Each `.bat` file passes a run key as a command-line argument (`east_coast`, `central`, or `west_coast`). `main.py` reads this via `sys.argv` and looks up the corresponding logistics groups, label, and region name from the `RUNS` dict.

### 2. Login
Selenium launches Chrome with a custom download directory set via `download.default_directory` prefs. The driver navigates to the TMS portal and authenticates using credentials loaded from a `.env` file.

### 3. Search
The pipeline navigates to the Tender Requests menu and sets search conditions:
- Carrier IDs filtered to target carriers
- Tender Request Status multi-selected via JavaScript (the select element is hidden)
- Logistics Group multi-selected via JavaScript — values vary per region
- Date range set to `TODAY` for both from and to

### 4. Column Customization
The List Customization panel is automated via JavaScript using the site's own `tmuiduallistboxmoveit` function — columns are moved, filtered, and reordered to match the required layout.

### 5. Export
The Export Data flow opens a popup window. The pipeline switches to the popup, submits, polls the download directory for the output file (up to 60 seconds), closes the popup, and returns to the main page.

### 6. Format & Send
The exported `.xlsx` file is formatted with openpyxl (column auto-fit + auto filter), then an HTML email is built with only the `Load ID` and `Tender Request Status` columns embedded as a table in the body. The formatted file is attached and sent via SMTP with BCC support.

### 7. Failure Alert
If all 5 export attempts fail, a separate failure alert email is sent to a different recipient list. The subject and body are kept concise.

---

## File Naming

Exported files are saved as `Report_{Region}_{mmddyyyy}.xlsx` (e.g. `Report_East_05042026.xlsx`). If a file for the same region and date already exists, it is overwritten. The pipeline keeps the most recent files — anything beyond the configured limit is deleted automatically on each run.

---

## Configuration

All settings are in `email_pipeline/email_setup.py`:

| Setting | Description |
|---------|-------------|
| `TMS_USER_ENV` / `TMS_PASS_ENV` | `.env` key names for TMS credentials |
| `ENV_PATH` | Path to the `.env` file |
| `DOWNLOAD_BASE` | Local folder where exports are saved |
| `MAX_DATA_FOLDERS` | Max number of export files to retain |
| `SMTP_SERVER` / `SMTP_PORT` | SMTP server settings |
| `SMTP_USER_ENV` / `SMTP_PASS_ENV` | `.env` key names for SMTP credentials |
| `NOTIFICATION_FROM` | Sender address |
| `EMAIL_TO` / `EMAIL_CC` / `EMAIL_BCC` | Report recipients |
| `EMAIL_SUBJECT` | Subject template — formatted with region and date |
| `EMAIL_TO_FAILURE` / `EMAIL_CC_FAILURE` | Failure alert recipients |
| `EMAIL_SUBJECT_FAILURE` | Failure alert subject template |

Credentials are never hardcoded — they are stored in a `.env` file and loaded at runtime via `python-dotenv`.

---

## Requirements

```
selenium
pandas
openpyxl
python-dotenv
```

Also requires `chromedriver.exe` placed at `C:\chromedriver.exe`.

---

## Running

Each region is triggered by its own bat file (intended for Task Scheduler):

```
run_east_coast.bat   →  python main.py east_coast
run_central.bat      →  python main.py central
run_west_coast.bat   →  python main.py west_coast
```

Or run directly:

```bash
python main.py east_coast
python main.py central
python main.py west_coast
```

---

## Changelog

### v1.3 — 2026-05-06 · Multi-Region Dispatch
- `RUNS` dict + `sys.argv` key — logistics groups resolved at runtime per region
- Single entry point replaces per-region scripts

### v1.2 — 2026-05-05 · Email Pipeline Hardening
- BCC support, failure alert email with separate recipient list
- File rotation — oldest exports pruned each run

### v1.1 — 2026-05-04 · Project Restructure
- Refactored into `email_pipeline/` + `utils/` module layout
- Added `project-overview.html`

### v1.0 — 2026-04-30 · Initial Release
- Selenium TMS login, tender search, column customization, export
- SMTP report distribution
