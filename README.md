# NEA Loss Analysis System v3 — Updated

Nepal Electricity Authority | Distribution Loss Report Management System

---

## WHAT'S CHANGED IN THIS VERSION

### 1. System Admin — Separate User (NOT the MD)
- New role: `SYS_ADMIN` — a system engineer who controls everything
- Login: `sysadmin / nea@admin123`
- Has full access to Django Admin panel at `/admin/`
- Can manage: Users, Organizations, Fiscal Years, Meter Points, Consumer Categories, all Reports
- **The MD is no longer the system admin** — MD is a separate view-only role

### 2. MD and DMD — Different Users, Same Rights
- MD login:  `md_user / nea@2024`
- DMD login: `dmd_user / nea@2024`
- Both have **identical navigation and permissions** (view-only)
- **"New Report" button removed** — they cannot create reports
- They can VIEW:
  - DC Reports (DCS-wise & Province-wise)
  - Provincial Reports
  - Analytics (DCS-wise & Province-wise)
  - Comparison (DCS-wise & Province-wise)
  - Organization Overview

### 3. Provincial Office — Create Monthly Report (auto-generated)
- **"New Report" button removed** — replaced with **"Create Monthly Report"**
- Login: `prov_kvdd / nea@2024`
- The monthly report is **auto-generated from DC reports** under that office
- Matches the provincial.xlsx format: S.N., DC Name, Received kWh, Utilised kWh, I.L.%, C.L.%, Total YTD, Target F.Y.
- Provincial manager can still review, approve, and reject DC reports

### 4. DC Staff — Unchanged
- Login: `dc_ktm / nea@2024` (Kathmandu), `dc_lpr / nea@2024` (Lalitpur), etc.
- Can create and submit monthly loss reports as before

---

## QUICK START

### Windows
1. Extract the zip
2. Double-click `start_windows.bat`
3. Browser opens at http://127.0.0.1:8000

### Linux / Mac
```bash
chmod +x start_linux_mac.sh
./start_linux_mac.sh
```

### Manual Start
```bash
# From the project folder (where manage.py is):
.venv\Scripts\python manage.py migrate          # Windows
.venv\Scripts\python manage.py seed_data        # Windows
.venv\Scripts\python manage.py runserver        # Windows

# or
.venv/bin/python manage.py migrate              # Linux/Mac
.venv/bin/python manage.py seed_data            # Linux/Mac
.venv/bin/python manage.py runserver            # Linux/Mac
```

---

## LOGIN CREDENTIALS

| Username    | Password      | Role                        | Access Level              |
|-------------|---------------|-----------------------------|---------------------------|
| `sysadmin`  | `nea@admin123`| System Administrator        | Full system control       |
| `md_user`   | `nea@2024`    | Managing Director           | View-only (reports/analytics) |
| `dmd_user`  | `nea@2024`    | Deputy Managing Director    | View-only (reports/analytics) |
| `prov_kvdd` | `nea@2024`    | Provincial Manager (KVDD)   | DC review + Prov. reports |
| `dc_ktm`    | `nea@2024`    | DC Staff (Kathmandu DC)     | Create & submit reports   |
| `dc_lpr`    | `nea@2024`    | DC Staff (Lalitpur DC)      | Create & submit reports   |
| `dc_nuw`    | `nea@2024`    | DC Staff (Nuwakot DC)       | Create & submit reports   |
| `dc_pkr`    | `nea@2024`    | DC Staff (Pokhara DC)       | Create & submit reports   |

**Django Admin Panel:** http://127.0.0.1:8000/admin/ (login with sysadmin / nea@admin123)

---

## NAVIGATION BY ROLE

### System Admin (sysadmin)
- Dashboard → full system stats + audit log
- All DC Reports + Provincial Reports
- Create DC Report, Create Provincial Report
- Analytics & Comparison
- **User Management** (create/edit all users, assign roles)
- **Django Admin Panel** (full DB control)

### MD / DMD (md_user / dmd_user)
- Dashboard → system-wide overview
- DC Reports (DCS-wise) — read only
- Provincial Reports — read only
- Analytics (DCS-wise & Province-wise)
- Comparison (DCS-wise & Province-wise)
- Organization Overview
- ❌ NO create/edit/delete report buttons

### Provincial Manager (prov_kvdd)
- Dashboard → office-level overview
- DC Reports (under their office) — can approve/reject
- **Create Monthly Report** → auto-generates from DC data in provincial.xlsx format
- Provincial Reports list
- Analytics & Comparison

### DC Staff (dc_ktm, dc_lpr, dc_nuw, dc_pkr)
- Dashboard → DC-level stats
- My Reports → list of their DC's reports
- **New Report** → create monthly loss report (full data entry)
- Analytics

---

## FILE STRUCTURE

```
nea_project/
├── manage.py
├── start_windows.bat          ← Double-click to run on Windows
├── start_linux_mac.sh         ← Run on Linux/Mac
├── db.sqlite3                 ← SQLite database (auto-created)
├── nea_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── nea_loss/
│   ├── models.py              ← SYS_ADMIN role + ProvincialReport model
│   ├── views.py               ← Updated permissions + ProvincialReportCreateView
│   ├── urls.py                ← Added provincial report URLs
│   ├── admin.py               ← Full admin panel for sysadmin
│   ├── context_processors.py ← Role flags: is_system_admin, can_create_provincial_report
│   ├── templatetags/
│   │   └── nea_filters.py    ← Additional template filters
│   ├── templates/
│   │   └── nea_loss/
│   │       ├── base.html      ← Role-based navigation
│   │       ├── reports/
│   │       │   ├── provincial_create.html  ← NEW: provincial report generator
│   │       │   ├── provincial_list.html    ← NEW: provincial reports list
│   │       │   └── ...existing templates
│   │       └── ...
│   ├── migrations/
│   │   └── 0005_add_provincial_report_sysadmin_role.py  ← NEW migration
│   └── management/
│       └── commands/
│           └── seed_data.py   ← Updated with all 8 users
└── .venv/                     ← Python virtual environment (Django 4.2)
```

---

## DATABASE

- SQLite (file: `db.sqlite3`)
- Automatically created on first run
- To reset: delete `db.sqlite3`, then run `migrate` and `seed_data` again

---

## MAKING CHANGES

- To add/edit users → login as `sysadmin` → go to `/admin/` → NEA Users
- To add DCs → `/admin/` → Distribution Centers
- To add Meter Points → `/admin/` → Meter Points
- To change FY target → `/admin/` → Fiscal Years → edit Loss Target %
- To change active FY → `/admin/` → Fiscal Years → tick "Is active"
- For code changes → edit files in `nea_loss/` folder

---

*NEA Loss Analysis System — Built for Nepal Electricity Authority*
