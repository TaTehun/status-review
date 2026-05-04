## Pipeline Overview
[View Pipeline Overview](https://tatehun.github.io/status-review/Pipeline-Overview.html)


# Tender Status Review — Automation Pipeline

An end-to-end Python automation pipeline that logs into a TMS web portal, queries today's tender requests, exports the results to Excel, and distributes a formatted report via email — with no manual steps.

---

## Overview

Each business day, load planners need to review the current tender status for specific carriers. This pipeline:

1. **Logs in** to the TMS portal via Selenium browser automation
2. **Searches** for today's tender requests filtered by carrier and status
3. **Customizes** the result columns to only include relevant fields
4. **Exports** the result set as an Excel file
5. **Formats** the file (column auto-fit, filters) and **sends** it via email with an embedded HTML summary table

---

## Project Structure

```
tender-status-review/
├── main.py                  # Full automation pipeline entry point
├── main_example.py          # Portfolio version (no sensitive values)
├── config.py                # All settings (paths, servers, recipients)
├── config_example.py        # Portfolio version of config
├── notifier.py              # SMTP email sender
├── utils/
│   ├── date_utils.py        # Date formatting utilities
│   └── email_utils.py       # xlsx formatting + HTML email body builder
└── brd/                     # Business requirement documents
```

---

## How It Works

### 1. Login
Selenium launches Chrome with a custom download directory set via `download.default_directory` prefs. The driver navigates to the TMS portal and authenticates using credentials loaded from a `.env` file.

### 2. Search
The pipeline navigates to the Tender Requests menu and sets search conditions:
- Carrier IDs filtered to target carriers
- Tender Request Status multi-selected via JavaScript (the select element is hidden, so direct interaction is not possible)
- Date range set to `TODAY` for both from and to

### 3. Column Customization
The List Customization panel is automated via JavaScript using the site's own `tmuiduallistboxmoveit` function — columns are moved, filtered, and reordered to match the required layout.

### 4. Export
The Export Data flow opens a popup window. The pipeline switches to the popup, submits, polls the download directory for the output file (up to 60 seconds), closes the popup, and returns to the main page.

### 5. Format & Send
The exported `.xlsx` file is formatted with openpyxl (column auto-fit + auto filter), then an HTML email is built with only the `Load ID` and `Tender Request Status` columns embedded as a table in the body. The formatted file is attached and sent via SMTP.

---

## File Management

Exported files are saved as `TenderStatus_MMDDYYYY.xlsx`. If a file for today already exists it is overwritten. The pipeline keeps the 5 most recent files — anything older is deleted automatically on each run.

---

## Configuration

All settings are in `config.py`:

| Setting | Description |
|---------|-------------|
| `TMS_URL` | TMS portal login URL |
| `TMS_USER_ENV` / `TMS_PASS_ENV` | `.env` key names for TMS credentials |
| `ENV_PATH` | Path to the `.env` file |
| `DOWNLOAD_BASE` | Local folder where exports are saved |
| `MAX_DATA_FOLDERS` | Max number of export files to retain |
| `SMTP_SERVER` / `SMTP_PORT` | SMTP server settings |
| `SMTP_USER_ENV` / `SMTP_PASS_ENV` | `.env` key names for SMTP credentials |
| `EMAIL_FROM` / `EMAIL_TO` / `EMAIL_CC` | Email sender and recipients |
| `EMAIL_SUBJECT` | Email subject template (formatted with today's date) |

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

```bash
python main.py
```

This runs the full pipeline: login → search → export → format → send.
