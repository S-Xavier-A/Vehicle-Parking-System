# ParkVault — Smart Parking System

A full-stack parking reservation web app built with Flask and SQLite. Users can find parking lots, reserve spots, and track their history. Admins can manage lots, monitor live reservations, and view revenue reports.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Default Accounts](#default-accounts)
- [User Guide](#user-guide)
- [Admin Guide](#admin-guide)
- [Project Structure](#project-structure)

---

## Features

**User**
- Register and log in securely (passwords hashed with bcrypt)
- Search parking lots by name, address, or PIN code
- Browse an interactive spot grid and reserve a specific spot
- View and release your active reservation with live cost calculation
- Full reservation history with CSV export

**Admin**
- Live dashboard showing active reservations with force-release controls
- Add, edit, and delete parking lots (spots auto-generated)
- Manage users — suspend or reactivate accounts
- Revenue reports with top-user leaderboard and daily breakdown
- Export all reservation data as CSV

---

## Requirements

- Python 3.9 or higher
- pip

All Python dependencies are listed in `requirements.txt`:

```
Flask==3.1.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-Bcrypt==1.0.1
Flask-Migrate==4.1.0
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

## Running the App

```bash
python run.py
```

On first run the app will:
- Create `parkvault.db` (SQLite database)
- Seed 6 parking lots with their spots
- Create a demo admin account and a demo user account

Then open your browser and go to:

```
http://localhost:5000
```

---

## Default Accounts

| Role  | Email                    | Password   |
|-------|--------------------------|------------|
| Admin | admin@parkvault.com      | admin123   |
| User  | arjun@example.com        | user123    |

> Change the `SECRET_KEY` in `run.py` before deploying to production.

---

## User Guide

### Register / Sign In

1. Open `http://localhost:5000`
2. Click **Create one** to register a new account, or sign in with an existing email and password
3. Fill in your name, email, phone, vehicle number, and a password

### Finding Parking

1. After logging in you land on the **Dashboard**
2. Click **Find Parking** in the sidebar or the button at the top right
3. Type a lot name, address, or PIN code in the search bar — or leave it blank to see all available lots
4. Filter by lot type (Open, Covered, Multi-level) using the dropdown
5. Lots that are full are shown greyed out and cannot be selected

### Reserving a Spot

1. Click any available lot card to open the **Select Spot** page
2. The interactive grid shows all spots — green means available, red means occupied
3. Click a green spot to select it
4. The reservation panel appears at the bottom showing your vehicle number, the current time, and the hourly rate
5. Adjust the start time if needed, then click **Confirm Reservation**
6. Confirm in the pop-up modal — the spot is now yours

### Releasing a Spot

1. Go to the **Dashboard** — the active reservation card shows your spot, duration, and running cost
2. Click **Release Spot**
3. Confirm in the modal — cost is calculated to the minute and saved to your history

### Viewing History

1. Click **History** in the sidebar
2. Toggle between **Table View** and **Timeline View** using the tabs at the top
3. Click **Download CSV** to export your full history as a spreadsheet

---

## Admin Guide

Log in with the admin account (`admin@parkvault.com` / `admin123`). You are redirected to the Admin Panel automatically.

### Dashboard (`/admin`)

- See total lots, spots, registered users, and how many spots are active right now
- The **Live Reservations** table lists every ongoing session with the user's name, vehicle, spot, duration, and running cost
- Click **Force Release** on any row to immediately end that session and calculate the final cost

### Managing Parking Lots (`/admin/lots`)

- The table shows all lots with real-time occupancy bars
- **Add New Lot** — fill in the name, address, PIN code, type, number of spots, and rate per hour. Spots are auto-generated (rows A–D, numbered 01–10 per row)
- **Edit (✏️)** — update any field; spot count cannot be reduced below the number of existing reservations
- **Delete (🗑️)** — permanently removes the lot and all its spots and reservation records (a confirmation dialog appears first)
- Use the search bar to filter the table instantly by name, address, or PIN

### Managing Users (`/admin/users`)

- Shows all non-admin registered users with their reservation count and total spend
- Use the search box to find a user by name, email, or vehicle number
- Navigate pages with the pagination controls at the bottom of the table
- **Suspend** — blocks the user from making new reservations; click again (shown as **Reactivate**) to restore access

### Reports & Revenue (`/admin/reports`)

- **Total Revenue** and **Total Reservations** are calculated from all completed sessions in the database
- **Top Users by Spend** — the five users who have spent the most overall
- **Daily Summary** — the last 7 days of activity showing reservation count and revenue per day
- Click **Export CSV** to download a full report of every reservation in the system

---

## Project Structure

```
Paking_app/
├── run.py                    # Flask app, all routes, seed logic
├── models.py                 # SQLAlchemy models (User, ParkingLot, Spot, Reservation)
├── requirements.txt          # Python dependencies
├── style.css                 # Global stylesheet (glassmorphism theme)
├── parkvault.db              # SQLite database (auto-created on first run)
│
├── index.html                # Sign-in page
├── register.html             # Registration page
├── user-dashboard.html       # User dashboard
├── search-parking.html       # Lot search results
├── spot-selection.html       # Interactive spot grid + reservation form
├── reservation-history.html  # User reservation history
│
├── admin-dashboard.html      # Admin overview + live reservations
├── admin-lots.html           # Parking lot management
├── admin-users.html          # User management
└── admin-reports.html        # Revenue reports
```

---

## Seeded Parking Lots

| Lot Name               | Area                    | PIN    | Type        | Spots | Rate    |
|------------------------|-------------------------|--------|-------------|-------|---------|
| Sarojini Nagar Hub     | Sarojini Nagar, Jaipur  | 302005 | Open        | 40    | ₹30/hr  |
| Civil Lines Parking    | Civil Lines, Jaipur     | 302006 | Covered     | 60    | ₹25/hr  |
| Pink City Mall Lot     | MI Road, Jaipur         | 302001 | Multi-level | 80    | ₹40/hr  |
| Railway Station Lot    | Jaipur Junction         | 302006 | Open        | 50    | ₹20/hr  |
| Vaishali Nagar Parking | Vaishali Nagar, Jaipur  | 302021 | Open        | 45    | ₹20/hr  |
| Mansarovar Complex     | Mansarovar, Jaipur      | 302020 | Covered     | 35    | ₹35/hr  |

---

## License

MIT
