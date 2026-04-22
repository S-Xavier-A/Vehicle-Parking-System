# ParkVault — Smart Parking Management System

A full-stack parking reservation web application built with **Flask** and **SQLite**. Users can search parking lots, reserve specific spots, and track their history. Admins get a complete management panel with live dashboards, revenue analytics, filterable reports, email alerts, and multi-level lot configuration.

> MCA Final Year Project — Jaipur, Rajasthan

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Email Alerts Setup](#email-alerts-setup)
- [Running the App](#running-the-app)
- [Default Accounts](#default-accounts)
- [User Guide](#user-guide)
- [Admin Guide](#admin-guide)
- [Database Models](#database-models)
- [Seeded Parking Lots](#seeded-parking-lots)

---

## Features

### User Portal
- Secure registration and login (passwords hashed with bcrypt)
- Search parking lots by name, address, or PIN code — filter by lot type
- Interactive spot grid — green (available), red (occupied), blue (selected)
- **Multi-level lot support** — spots displayed per floor (Level 1, Level 2…)
- One-click spot reservation with live cost estimate
- Active reservation card on dashboard with real-time duration and cost
- Release spot with instant cost calculation (charged per minute)
- Full reservation history — table view and timeline view
- CSV export of personal reservation history
- Dark / Light theme toggle (persisted in localStorage)

### Admin Panel
- Live dashboard with total lots, spots, users, and all active sessions
- Force-release any active reservation from the dashboard
- **Parking Lot Management** — add, edit, delete lots; spots auto-generated
- **Multi-level lot builder** — specify number of floors and spots per floor; spots named `L1-A-01`, `L2-A-01`…
- **User Management** — search, paginate, suspend/reactivate, promote to admin, add/edit/delete users
- **Filterable Reports** — filter by date range, specific users, specific lots; 4 KPI cards, top users, daily breakdown, lot revenue bars, full detail table
- **CSV export** of filtered reports with dynamic filenames
- **Raw SQL console** — execute any query against the live database
- Database schema viewer with row counts per table
- **Email Alerts** — automated booking confirmations, receipts, long-stay reminders, daily admin summaries, on-demand monthly reports
- Full dark / light theme support across all admin pages

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.9+, Flask 3.1 |
| ORM | Flask-SQLAlchemy (SQLite) |
| Auth | Flask-Login, Flask-Bcrypt |
| Email | Flask-Mail (Gmail SMTP / any SMTP) |
| Scheduler | APScheduler (background jobs) |
| Frontend | Jinja2 templates, Vanilla JS, CSS custom properties |
| Theme | Glassmorphism — dark/light with CSS variables |
| Export | Python `csv` module (UTF-8 BOM for Excel compatibility) |

---

## Project Structure

```
Paking_app/
│
├── run.py                    # Flask app — all routes, helpers, email functions, scheduler
├── models.py                 # SQLAlchemy models: User, ParkingLot, Spot, Reservation
├── requirements.txt          # Python dependencies
├── style.css                 # Global stylesheet (glassmorphism, dark + light themes)
├── .env.example              # Template for email environment variables
├── parkvault.db              # SQLite database (auto-created on first run)
│
│── User-facing pages ───────────────────────────────────────────────────────────
├── index.html                # Sign-in page
├── register.html             # Registration page
├── user-dashboard.html       # Dashboard — stats, active reservation, recent history
├── search-parking.html       # Lot search and filter results
├── spot-selection.html       # Interactive spot grid + reservation confirmation
├── reservation-history.html  # Full history — table view & timeline view
│
└── Admin pages ─────────────────────────────────────────────────────────────────
    ├── admin-dashboard.html  # Live overview + force-release controls
    ├── admin-lots.html       # Lot management + multi-level builder modal
    ├── admin-users.html      # User management + CRUD modals
    ├── admin-reports.html    # Filterable reports, KPIs, charts, CSV export
    └── admin-database.html   # Raw SQL console + schema inspector
```

---

## Requirements

- Python 3.9 or higher
- pip

Install all dependencies with:

```bash
pip install -r requirements.txt
```

**`requirements.txt`**
```
Flask==3.1.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-Bcrypt==1.0.1
Flask-Migrate==4.1.0
Flask-Mail==0.10.0
APScheduler==3.11.2
gunicorn
```

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/your-username/Paking_app.git
cd Paking_app
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

---

## Email Alerts Setup

Email alerts are **optional** — the app runs fine without them (emails are silently skipped when credentials are not set).

To enable real email sending:

**Step 1 — Create a Gmail App Password**
1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Security → 2-Step Verification (must be ON)
3. Security → App Passwords → Select app: Mail → **Generate**
4. Copy the 16-character password shown

**Step 2 — Set environment variables before starting the server**

```bash
# macOS / Linux
export MAIL_USERNAME=yourapp@gmail.com
export MAIL_PASSWORD="xxxx xxxx xxxx xxxx"
python run.py
```

```powershell
# Windows PowerShell
$env:MAIL_USERNAME="yourapp@gmail.com"
$env:MAIL_PASSWORD="xxxx xxxx xxxx xxxx"
python run.py
```

See `.env.example` for all available configuration options.

### Emails sent automatically

| Email | Trigger | Recipient |
|---|---|---|
| Booking Confirmation | User reserves a spot | The user |
| Parking Receipt | Spot is released | The user |
| Long-stay Reminder | Every hour — users parked 2+ hours | The parked user |
| Daily Admin Summary | Every day at 8:00 AM | All admins |
| Monthly Report | Admin clicks "Send Monthly Report" | All admins |

---

## Running the App

```bash
python run.py
```

On first run the app will automatically:
- Create `parkvault.db` (SQLite database)
- Seed 6 parking lots with all their spots pre-generated
- Create 2 admin accounts and 8 demo user accounts

Then open your browser:

```
http://localhost:5001
```

> **Port already in use?**
> ```bash
> lsof -ti :5001 | xargs kill -9
> ```

---

## Default Accounts

### Admin Accounts

| Name | Email | Password |
|---|---|---|
| Super Admin | admin@parkvault.com | admin123 |
| Xavier Ops | xavier@parkvault.com | xavier123 |

### Demo User Accounts

| Name | Email | Password |
|---|---|---|
| Aarav Sharma | aarav@example.com | user123 |
| Priya Mehta | priya@example.com | user123 |
| Rohan Verma | rohan@example.com | user123 |
| Sneha Gupta | sneha@example.com | user123 |
| Karan Singh | karan@example.com | user123 |
| Anjali Patel | anjali@example.com | user123 |

> **Security note:** Change `SECRET_KEY` in `run.py` before deploying to production.

---

## User Guide

### Register / Sign In

1. Open `http://localhost:5001`
2. Click **Create one** to register, or sign in with an existing account
3. Fill in name, email, phone, vehicle number, and password

### Finding Parking

1. After login you land on the **Dashboard**
2. Click **Find Parking** in the sidebar or the top-right button
3. Search by lot name, address, or PIN code — or leave blank to see all lots
4. Filter by type: Open, Covered, or Multi-level
5. Each lot card shows available spots, rate, and lot type

### Reserving a Spot

1. Click a lot card → **Select Spot** page opens
2. For multi-level lots, spots are grouped by floor — **Level 1**, **Level 2**, etc.
3. Green spots are available — click one to select it
4. A confirmation panel appears at the bottom with your vehicle and the rate
5. Click **Confirm Reservation** → confirm in the modal

### Releasing a Spot

1. Go to the **Dashboard** — the active reservation card shows spot, duration, and running cost
2. Click **Release Spot** → confirm in the modal
3. Final cost is saved to your history; a receipt email is sent automatically

### Viewing History

1. Click **History** in the sidebar
2. Switch between **Table View** and **Timeline View** using the tabs
3. Click **Download CSV** to export your full history

---

## Admin Guide

Log in with an admin account — you are redirected to the Admin Panel automatically.

### Dashboard (`/admin`)

- Overview cards: total lots, total spots, registered users, available spots right now
- **Live Reservations** table — user, vehicle, lot, spot, check-in time, duration, running cost
- **Force Release** button on any row ends that session and calculates the final bill

### Parking Lots (`/admin/lots`)

- Occupancy bar for every lot (green → amber → red as occupancy rises)
- **Add New Lot** modal:
  - For **Open / Covered** lots: enter total spots — spots are auto-named `A-01`, `A-02`… `B-01`…
  - For **Multi-level** lots: enter number of floors and spots per floor — spots are named `L1-A-01`, `L2-A-01`… per level
- **Edit (✏️)** — update name, type, address, rate, status
- **Delete (🗑️)** — removes lot, all its spots, and reservation records (confirmation required)

### Users (`/admin/users`)

- Search by name, email, or vehicle number
- Paginated table with booking count and total spend per user
- **Suspend / Reactivate** — blocks or restores login access
- **Promote / Demote** — toggle admin role (cannot change own role)
- **Edit / Delete** users with full CRUD modals

### Reports & Revenue (`/admin/reports`)

- **Filters** — date range (from/to), specific users (multi-select), specific lots (multi-select), quick presets (Today, This Week, This Month, Last 30/90 Days, This Year)
- **4 KPI cards** — Total Revenue, Completed Sessions, Avg Cost/Session, Unique Users
- **Top 5 Users** by spend
- **Daily Breakdown** — last 14 days of sessions and revenue
- **Revenue by Parking Lot** — horizontal bar chart
- **Full detail table** — every reservation matching the current filters
- **Export CSV** — downloads filtered data; filename includes the selected date range
- **Send Monthly Report** — emails this month's stats to all admin accounts

### Database (`/admin/database`)

- **Raw SQL Console** — run any SELECT, INSERT, UPDATE, or DELETE against the live DB; results shown in a formatted table with execution time
- **Schema Explorer** — all tables with column names, types, and row counts
- **Export Users CSV** — full user data export

---

## Database Models

```
User
├── id, first_name, last_name, email, password_hash
├── phone, vehicle, status (active / parked / suspended)
├── is_admin, joined
└── → reservations

ParkingLot
├── id, name, address, pin_code, lot_type (open / covered / multi-level)
├── total_spots, rate_per_hour, status (active / inactive)
├── → spots
└── → reservations

Spot
├── id, lot_id (FK), spot_number
└── is_occupied

Reservation
├── id, user_id (FK), lot_id (FK)
├── spot_number, check_in, check_out, cost
└── status (active / completed / cancelled)
```

---

## Seeded Parking Lots

| Lot Name | Area | PIN | Type | Spots | Rate |
|---|---|---|---|---|---|
| Sarojini Nagar Hub | Sarojini Nagar, Jaipur | 302005 | Open | 40 | ₹30/hr |
| Civil Lines Parking | Civil Lines, Jaipur | 302006 | Covered | 60 | ₹25/hr |
| Pink City Mall Lot | MI Road, Jaipur | 302001 | Multi-level | 80 | ₹40/hr |
| Railway Station Lot | Jaipur Junction | 302006 | Open | 50 | ₹20/hr |
| Vaishali Nagar Parking | Vaishali Nagar, Jaipur | 302021 | Open | 45 | ₹20/hr |
| Mansarovar Complex | Mansarovar, Jaipur | 302020 | Covered | 35 | ₹35/hr |

---

## License

MIT
