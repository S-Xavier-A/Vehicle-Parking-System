"""
ParkVault — Project Documentation PDF Generator
Run: python generate_pdf.py
Output: ParkVault_Project_Documentation.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Flowable
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "ParkVault_Project_Documentation.pdf")

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0d1b3e")
ACCENT     = colors.HexColor("#4facfe")
ACCENT2    = colors.HexColor("#00e887")
LIGHT_BG   = colors.HexColor("#eef4ff")
HEADER_BG  = colors.HexColor("#1a2d5a")
ROW_ALT    = colors.HexColor("#f0f5ff")
MUTED      = colors.HexColor("#5a6a8a")
WHITE      = colors.white
BLACK      = colors.HexColor("#0d1527")
RULE_COLOR = colors.HexColor("#c8d8f0")
CODE_BG    = colors.HexColor("#f0f4fa")
CODE_FG    = colors.HexColor("#1a3560")

# ── Styles ────────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    styles = {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName="Helvetica-Bold",
            fontSize=34,
            textColor=WHITE,
            spaceAfter=8,
            alignment=TA_CENTER,
            leading=40,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontName="Helvetica",
            fontSize=14,
            textColor=colors.HexColor("#a8c8f8"),
            spaceAfter=6,
            alignment=TA_CENTER,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            fontName="Helvetica",
            fontSize=11,
            textColor=colors.HexColor("#c8deff"),
            spaceAfter=4,
            alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=NAVY,
            spaceBefore=18,
            spaceAfter=6,
            leading=22,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=HEADER_BG,
            spaceBefore=14,
            spaceAfter=4,
            leading=17,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=colors.HexColor("#2a4a8a"),
            spaceBefore=10,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            textColor=BLACK,
            spaceAfter=6,
            leading=15,
            alignment=TA_JUSTIFY,
        ),
        "body_left": ParagraphStyle(
            "body_left",
            fontName="Helvetica",
            fontSize=10,
            textColor=BLACK,
            spaceAfter=4,
            leading=15,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=10,
            textColor=BLACK,
            spaceAfter=3,
            leading=14,
            leftIndent=16,
            bulletIndent=4,
        ),
        "code": ParagraphStyle(
            "code",
            fontName="Courier",
            fontSize=8.5,
            textColor=CODE_FG,
            spaceAfter=2,
            leading=13,
            leftIndent=0,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName="Helvetica-Oblique",
            fontSize=9,
            textColor=MUTED,
            spaceAfter=10,
            alignment=TA_CENTER,
        ),
        "note": ParagraphStyle(
            "note",
            fontName="Helvetica-Oblique",
            fontSize=9,
            textColor=colors.HexColor("#3a5a9a"),
            spaceAfter=6,
            leading=13,
        ),
    }
    return styles


# ── Helper flowables ──────────────────────────────────────────────────────────
class ColorRect(Flowable):
    """A filled rectangle used as section-header background."""
    def __init__(self, width, height, fill_color, radius=6):
        super().__init__()
        self.width = width
        self.height = height
        self.fill_color = fill_color
        self.radius = radius

    def draw(self):
        self.canv.setFillColor(self.fill_color)
        self.canv.roundRect(0, 0, self.width, self.height, self.radius, fill=1, stroke=0)


def section_header(text, styles, accent=ACCENT):
    """Returns a styled section header as a list of flowables."""
    return [
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=2, color=accent, spaceAfter=4),
        Paragraph(text, styles["h1"]),
    ]


def subsection(text, styles):
    return [Paragraph(text, styles["h2"])]


def code_block(lines, styles, bg=CODE_BG):
    """Returns a code block table."""
    content = "\n".join(lines)
    paras = [Paragraph(line.replace(" ", "&nbsp;").replace("<", "&lt;").replace(">", "&gt;"),
                       styles["code"])
             for line in lines]
    t = Table([[p] for p in paras],
              colWidths=["100%"],
              hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ("ROUNDEDCORNERS", [6]),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE_COLOR),
    ]))
    return [t, Spacer(1, 6)]


def data_table(headers, rows, styles, col_widths=None):
    """Returns a styled data table."""
    header_row = [Paragraph(f"<b>{h}</b>", ParagraphStyle(
        "th", fontName="Helvetica-Bold", fontSize=9,
        textColor=WHITE, alignment=TA_LEFT
    )) for h in headers]
    data_rows = []
    for row in rows:
        data_rows.append([
            Paragraph(str(cell), ParagraphStyle(
                "td", fontName="Helvetica", fontSize=9,
                textColor=BLACK, leading=13
            )) for cell in row
        ])
    all_rows = [header_row] + data_rows
    t = Table(all_rows, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    style = TableStyle([
        # Header
        ("BACKGROUND",   (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        ("TOPPADDING",   (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING",(0, 0), (-1, 0), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        # Body rows
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("TOPPADDING",   (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ("GRID",         (0, 0), (-1, -1), 0.4, RULE_COLOR),
        ("LINEABOVE",    (0, 1), (-1, 1), 1, RULE_COLOR),
        ("ROUNDEDCORNERS", [4]),
    ])
    t.setStyle(style)
    return [t, Spacer(1, 8)]


# ── Cover page ────────────────────────────────────────────────────────────────
def cover_page(styles):
    elements = []

    # Dark background block (simulated with a colored table)
    cover_data = [[""]]
    cover_table = Table(cover_data, colWidths=[19*cm], rowHeights=[6*cm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("ROUNDEDCORNERS", [10]),
    ]))

    # Title block
    title_content = [
        Spacer(1, 2*cm),
        Paragraph("🅿 ParkVault", styles["cover_title"]),
        Paragraph("Smart Parking Management System", styles["cover_sub"]),
        Spacer(1, 0.5*cm),
        HRFlowable(width="60%", thickness=1, color=ACCENT, spaceAfter=16, hAlign="CENTER"),
        Paragraph("MCA Final Year Project", styles["cover_meta"]),
        Paragraph("Complete Technical Documentation", styles["cover_meta"]),
        Spacer(1, 0.4*cm),
        Paragraph("Technology: Python · Flask · SQLite · SQLAlchemy · Jinja2 · HTML5 / CSS3", styles["cover_meta"]),
        Spacer(1, 2*cm),
    ]

    # Wrap in a colored background table
    bg_table = Table([[title_content]], colWidths=[19*cm])
    bg_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 30),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 30),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
        ("ROUNDEDCORNERS", [10]),
    ]))
    elements.append(bg_table)
    elements.append(Spacer(1, 0.6*cm))

    # Info cards row
    info_items = [
        ["Domain", "Parking Management / Smart City"],
        ["Platform", "Web Application (Browser-based)"],
        ["Backend", "Python 3 + Flask Framework"],
        ["Database", "SQLite via SQLAlchemy ORM"],
        ["Frontend", "HTML5, CSS3, Vanilla JavaScript"],
        ["Users", "Regular Users + Admin Panel"],
    ]
    info_rows = [[
        Paragraph(f"<b>{k}</b>", ParagraphStyle("ik", fontName="Helvetica-Bold",
                  fontSize=9, textColor=MUTED)),
        Paragraph(v, ParagraphStyle("iv", fontName="Helvetica", fontSize=10,
                  textColor=BLACK))
    ] for k, v in info_items]
    info_table = Table(info_rows, colWidths=[4*cm, 14*cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BG),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID",          (0, 0), (-1, -1), 0.3, RULE_COLOR),
        ("ROUNDEDCORNERS", [6]),
    ]))
    elements.append(info_table)
    elements.append(PageBreak())
    return elements


# ── Table of Contents ─────────────────────────────────────────────────────────
def toc(styles):
    items = [
        ("1.", "Project Overview"),
        ("2.", "Technology Stack & Dependencies"),
        ("3.", "Project File Structure"),
        ("4.", "Database Design — The Four Models"),
        ("5.", "Application Architecture — MVC Pattern"),
        ("6.", "Control Flow — Operation by Operation"),
        ("  6.1", "Application Startup"),
        ("  6.2", "User Registration"),
        ("  6.3", "Login Flow"),
        ("  6.4", "Search for Parking"),
        ("  6.5", "Spot Selection"),
        ("  6.6", "Reservation (Booking)"),
        ("  6.7", "Check-Out / Billing"),
        ("  6.8", "Admin — Force Release"),
        ("  6.9", "Admin — Lot Management"),
        ("  6.10", "Reports & Analytics"),
        ("  6.11", "CSV Export"),
        ("7.", "Authentication & Security Layers"),
        ("8.", "Theme System (Dark / Light Mode)"),
        ("9.", "Data Flow Diagram"),
        ("10.", "Key Design Decisions"),
    ]
    elements = [Paragraph("Table of Contents", styles["h1"]), Spacer(1, 4)]
    for num, title in items:
        bold = not num.startswith(" ")
        style = ParagraphStyle("toci", fontName="Helvetica-Bold" if bold else "Helvetica",
                               fontSize=10 if bold else 9.5,
                               textColor=NAVY if bold else BLACK,
                               spaceAfter=4, leftIndent=0 if bold else 20)
        elements.append(Paragraph(f"{num}&nbsp;&nbsp;&nbsp;{title}", style))
    elements.append(PageBreak())
    return elements


# ── Main content ──────────────────────────────────────────────────────────────
def build_content(styles):
    S = styles
    elements = []
    B  = S["body"]
    BL = S["body_left"]
    H1 = S["h1"]
    H2 = S["h2"]
    H3 = S["h3"]
    BU = S["bullet"]

    def h(text):
        return section_header(text, S)

    def sub(text):
        return subsection(text, S)

    def p(text, st=None):
        return Paragraph(text, st or B)

    def sp(n=6):
        return Spacer(1, n)

    def hr():
        return HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=6)

    # ── Section 1 ─────────────────────────────────────────────────────────────
    elements += h("1. Project Overview")
    elements.append(p(
        "<b>ParkVault</b> is a web-based <b>Smart Parking Management System</b> designed for "
        "urban parking lots. It serves two types of users — <b>regular users</b> (drivers) who "
        "find and reserve parking spots, and <b>administrators</b> who manage lots, users, and "
        "revenue reports. The system tracks reservations in real time and automatically calculates "
        "billing per minute based on actual parking duration using server-side timestamps."
    ))
    elements.append(p(
        "The application is built entirely with open-source technologies, requiring no paid services, "
        "no cloud infrastructure, and no frontend build tools — making it ideal for academic deployment "
        "and demonstration on any machine with Python installed."
    ))

    # ── Section 2 ─────────────────────────────────────────────────────────────
    elements += h("2. Technology Stack &amp; Dependencies")
    elements += data_table(
        ["Layer", "Technology", "Purpose"],
        [
            ["Backend", "Python 3.14 + Flask", "Web server, routing, all business logic"],
            ["Database", "SQLite via SQLAlchemy ORM", "Persistent data storage — single file, zero config"],
            ["Authentication", "Flask-Login + Flask-Bcrypt", "Session management, bcrypt password hashing"],
            ["Templating", "Jinja2 (built into Flask)", "Dynamic HTML rendered on the server side"],
            ["Frontend", "HTML5 + CSS3 + Vanilla JS", "UI and interactivity (no JS framework needed)"],
            ["Styling", "Custom CSS (Glassmorphism)", "Dark/light theme, responsive layout"],
            ["Package Manager", "pip + virtualenv (.venv)", "Isolated Python dependency environment"],
        ],
        S, col_widths=[3.5*cm, 5.5*cm, 9*cm]
    )
    elements.append(p("<b>Python packages (requirements.txt):</b>", BL))
    for pkg, desc in [
        ("flask", "The core web framework — handles routing, request/response, templating"),
        ("flask-sqlalchemy", "ORM bridge — maps Python classes to SQLite database tables"),
        ("flask-login", "Manages logged-in user sessions using secure HTTP cookies"),
        ("flask-bcrypt", "Hashes passwords using the bcrypt algorithm before storing in DB"),
    ]:
        elements.append(p(f"• <b>{pkg}</b> — {desc}", BU))

    # ── Section 3 ─────────────────────────────────────────────────────────────
    elements += h("3. Project File Structure")
    elements += code_block([
        "Paking_app/",
        "│",
        "├── run.py                   ← Main application (all routes + business logic)",
        "├── models.py                ← Database schema (4 tables as Python classes)",
        "├── style.css                ← Complete stylesheet (dark + light theme)",
        "│",
        "├── index.html               ← Login page",
        "├── register.html            ← User registration page",
        "├── user-dashboard.html      ← User home after login",
        "├── search-parking.html      ← Find available parking lots",
        "├── spot-selection.html      ← Visual spot grid for a chosen lot",
        "├── reservation-history.html ← User's booking history (table + timeline)",
        "│",
        "├── admin-dashboard.html     ← Admin home (live reservations overview)",
        "├── admin-lots.html          ← Manage parking lots (add/edit/delete)",
        "├── admin-users.html         ← Manage registered users",
        "├── admin-reports.html       ← Revenue analytics + top users",
        "├── admin-database.html      ← Raw DB browser + live SQL workspace",
        "│",
        "└── instance/",
        "    └── parkvault.db         ← SQLite database file (auto-created on startup)",
    ], S)
    elements.append(p(
        "<i>Note: Flask is configured with <b>template_folder='.'</b> and "
        "<b>static_folder='.'</b>, so all HTML and CSS files sit in the project root "
        "rather than separate templates/ and static/ directories.</i>", S["note"]
    ))

    # ── Section 4 ─────────────────────────────────────────────────────────────
    elements += h("4. Database Design — The Four Models")
    elements.append(p(
        "All tables are defined in <b>models.py</b> using Flask-SQLAlchemy as Python classes. "
        "SQLAlchemy translates these into SQL CREATE TABLE statements automatically. "
        "The four models and their relationships are:"
    ))
    elements += code_block([
        "User  ──< Reservation >──  ParkingLot",
        "                               │",
        "                             Spot  (linked to ParkingLot via lot_id FK)",
    ], S)

    elements += sub("4.1  User Table")
    elements += data_table(
        ["Column", "Type", "Description"],
        [
            ["id", "Integer PK", "Auto-incrementing primary key"],
            ["first_name, last_name", "String(60)", "User's full name — combined as user.name property"],
            ["email", "String(120) UNIQUE", "Used as the login credential — must be unique"],
            ["password_hash", "String(256)", "bcrypt hash of the password — never stored as plain text"],
            ["phone", "String(20)", "Optional contact number"],
            ["vehicle", "String(50)", "Vehicle registration number shown in reservations"],
            ["status", "String", "'active' / 'parked' / 'suspended' — reflects current state"],
            ["is_admin", "Boolean", "True → Admin Portal access; False → User Portal"],
            ["joined", "DateTime", "Auto-set to current timestamp at account creation"],
        ],
        S, col_widths=[4.5*cm, 4*cm, 10*cm]
    )

    elements += sub("4.2  ParkingLot Table")
    elements += data_table(
        ["Column", "Type", "Description"],
        [
            ["id", "Integer PK", "Auto-incrementing primary key"],
            ["name", "String(100)", "Lot display name, e.g. 'Sarojini Nagar Hub'"],
            ["address, pin_code", "String", "Location info — used in search/filter"],
            ["lot_type", "String", "'open' / 'covered' / 'multi-level'"],
            ["total_spots", "Integer", "Used to calculate occupancy percentage"],
            ["rate_per_hour", "Float", "e.g. 30.0 (₹) — used in billing formula"],
            ["status", "String", "'active' (shown in search) / 'inactive' (hidden)"],
        ],
        S, col_widths=[4.5*cm, 3.5*cm, 10.5*cm]
    )

    elements += sub("4.3  Spot Table")
    elements += data_table(
        ["Column", "Type", "Description"],
        [
            ["id", "Integer PK", "Auto-incrementing primary key"],
            ["lot_id", "FK → parking_lot.id", "Which lot this spot belongs to"],
            ["spot_number", "String(10)", "e.g. 'A-01', 'B-07' — Row-Number format"],
            ["is_occupied", "Boolean", "True when a car is currently parked; False when free"],
        ],
        S, col_widths=[4.5*cm, 4*cm, 10*cm]
    )
    elements.append(p(
        "<i>A UNIQUE constraint on (lot_id, spot_number) prevents duplicate spot records per lot.</i>", S["note"]
    ))

    elements += sub("4.4  Reservation Table")
    elements += data_table(
        ["Column", "Type", "Description"],
        [
            ["id", "Integer PK", "Auto-incrementing primary key"],
            ["user_id", "FK → user.id", "Which user made this reservation"],
            ["lot_id", "FK → parking_lot.id", "Which lot they parked in"],
            ["spot_number", "String(10)", "Which specific spot (e.g. 'C-04')"],
            ["check_in", "DateTime", "Server time when reservation was created"],
            ["check_out", "DateTime (nullable)", "Server time when user released the spot"],
            ["cost", "Float (nullable)", "Calculated only at check-out; NULL while active"],
            ["status", "String", "'active' / 'completed' / 'cancelled'"],
        ],
        S, col_widths=[4.5*cm, 4*cm, 10*cm]
    )

    # ── Section 5 ─────────────────────────────────────────────────────────────
    elements += h("5. Application Architecture — MVC Pattern")
    elements.append(p(
        "ParkVault follows the <b>Model-View-Controller (MVC)</b> architectural pattern:"
    ))
    elements.append(p("• <b>Model</b> — The four SQLAlchemy classes in models.py (User, ParkingLot, Spot, Reservation)", BU))
    elements.append(p("• <b>View</b> — The HTML template files, rendered dynamically by Jinja2", BU))
    elements.append(p("• <b>Controller</b> — The route functions in run.py, which receive requests, query the DB, and return rendered pages", BU))
    elements.append(sp())
    elements += code_block([
        "Browser (View)",
        "    │  HTTP GET / POST request",
        "    ▼",
        "Flask Route in run.py  (Controller)",
        "    │  Query / Update via SQLAlchemy",
        "    ▼",
        "SQLite Database  (Model)",
        "    │  Returns data objects",
        "    ▼",
        "Jinja2 renders HTML template  (View)",
        "    │  HTTP Response with complete HTML page",
        "    ▼",
        "Browser displays the page",
    ], S)
    elements.append(p(
        "There is <b>no separate REST API</b>. Data is embedded directly into the HTML "
        "by Jinja2 using template tags like <b>{{ variable }}</b>, <b>{% for %}</b>, and "
        "<b>{% if %}</b>. JavaScript is only used for client-side UI interactions "
        "(spot grid rendering, modals, theme toggle) — not for fetching data."
    ))

    # ── Section 6 ─────────────────────────────────────────────────────────────
    elements += h("6. Control Flow — Operation by Operation")

    # 6.1
    elements += sub("6.1  Application Startup")
    elements += code_block([
        "$ python run.py",
        "  → Flask app object created with SECRET_KEY and DB URI",
        "  → db.create_all()     ← creates all 4 tables if they don't exist",
        "  → seed_db()           ← checks if DB is empty; if so, inserts:",
        "        2 admin accounts + 8 regular users",
        "        6 parking lots (5 active, 1 inactive)",
        "        310 spot records auto-generated using naming formula:",
        "            Spots 1-10  → Row A  (A-01 to A-10)",
        "            Spots 11-20 → Row B  (B-01 to B-10)  ... and so on",
        "  → Flask dev server starts on port 5001",
    ], S)

    # 6.2
    elements += sub("6.2  User Registration Flow")
    elements += code_block([
        "GET /register",
        "  → render register.html (blank form shown)",
        "",
        "POST /register  (form submitted)",
        "  → Validate: do passwords match?",
        "  → Check: does email already exist in User table?",
        "  → bcrypt.generate_password_hash(password)  ← one-way hash with salt",
        "  → New User object saved to DB",
        "  → login_user(user)  ← Flask-Login sets session cookie in browser",
        "  → redirect to /dashboard",
    ], S)

    # 6.3
    elements += sub("6.3  Login Flow")
    elements += code_block([
        "GET /",
        "  → If already logged in → redirect to /admin or /dashboard",
        "  → Else → render index.html (login form)",
        "",
        "POST /login",
        "  → User.query.filter_by(email=email).first()  ← DB lookup",
        "  → bcrypt.check_password_hash(stored_hash, entered_password)",
        "  → If match → login_user(user)",
        "      is_admin=True  → redirect to /admin",
        "      is_admin=False → redirect to /dashboard",
        "  → If no match → flash('Invalid email or password.') → redirect to /",
    ], S)
    elements.append(p(
        "<b>Security note:</b> Passwords are never stored as plain text. bcrypt applies a one-way "
        "hash with a random salt, so even if the database file is accessed directly, "
        "original passwords cannot be recovered.", S["note"]
    ))

    # 6.4
    elements += sub("6.4  Searching for Parking")
    elements += code_block([
        "GET /search?q=302001&type=covered",
        "  → @login_required  ← redirect to login if no valid session cookie",
        "  → Build SQL query: ParkingLot WHERE status='active'",
        "  → If q provided: filter name / address / pin_code (case-insensitive LIKE)",
        "  → If type provided: filter lot_type = 'open' / 'covered' / 'multi-level'",
        "  → For each lot: count free spots (Spot WHERE is_occupied=False)",
        "  → render_template('search-parking.html', lots=lots)",
        "  → Jinja2 loop renders one card per lot with live availability data",
    ], S)

    # 6.5
    elements += sub("6.5  Spot Selection Flow")
    elements += code_block([
        "GET /spots?lot_id=3",
        "  → Fetch ParkingLot record by lot_id",
        "  → Fetch all Spot records for that lot, ordered by spot_number",
        "  → Pass to template: lot, spots list, free_count",
        "",
        "In the Browser (JavaScript):",
        "  → Jinja2 injects occupied spot IDs into JS:  const occupiedSpots = new Set([...])",
        "  → buildGrid() groups spots by row letter (A, B, C, D...)",
        "  → Each spot rendered as a div:",
        "       Green border = available  → onclick calls selectSpot()",
        "       Red border   = occupied   → no click handler",
        "  → When user clicks a spot:",
        "       Selected spot highlighted in blue",
        "       'Reserve Spot' panel slides into view",
        "       Current IST time auto-filled in the time field",
        "  → User clicks 'Confirm Reservation':",
        "       Confirmation modal shown with spot + rate details",
        "       User confirms → hidden <form> submitted via POST /reserve",
    ], S)

    # 6.6
    elements += sub("6.6  Reservation (Booking) Flow")
    elements += code_block([
        "POST /reserve",
        "  → Receive: lot_id, spot_number from form",
        "  → Re-validate in DB: Spot WHERE lot_id=X AND spot_number=Y AND is_occupied=False",
        "     (protects against race condition — two users clicking same spot simultaneously)",
        "  → If spot gone: flash message → redirect back to spot selection",
        "  → If available:",
        "       check_in = datetime.now()   ← server time, NOT client time",
        "       New Reservation(status='active') added to DB",
        "       spot.is_occupied = True",
        "       current_user.status = 'parked'",
        "       db.session.commit()",
        "  → redirect to /dashboard",
    ], S)
    elements.append(p(
        "<b>Why server time?</b> Using datetime.now() on the server prevents manipulation — "
        "a user cannot change their phone/computer clock to get a cheaper bill.", S["note"]
    ))

    # 6.7
    elements += sub("6.7  Check-Out and Billing Calculation")
    elements += code_block([
        "POST /release  (user clicks 'Release Spot')",
        "  → Verify: res.user_id == current_user.id  ← security ownership check",
        "  → Call _release_reservation(res):",
        "",
        "      def _release_reservation(res):",
        "          res.check_out = datetime.now()",
        "          secs = (res.check_out - res.check_in).total_seconds()",
        "          res.cost = round((secs / 3600) * res.lot.rate_per_hour, 2)",
        "          res.status = 'completed'",
        "          spot.is_occupied = False",
        "          if no other active reservations: user.status = 'active'",
        "          db.session.commit()",
        "",
        "  → redirect to /dashboard",
    ], S)
    elements.append(p(
        "<b>Billing formula:</b> Cost (₹) = (Seconds parked ÷ 3600) × Rate per hour. "
        "This charges per-second (effectively per-minute). Example: 90 minutes at ₹40/hr "
        "= 90/60 × 40 = <b>₹60.00</b> exactly.", S["note"]
    ))

    # 6.8
    elements += sub("6.8  Admin — Force Release")
    elements.append(p(
        "When an admin clicks <b>Force Release</b> on the dashboard live reservations table:"
    ))
    elements += code_block([
        "POST /admin/release/<res_id>",
        "  → @login_required + @admin_required  ← two decorator checks",
        "  → Same _release_reservation(res) helper called",
        "  → redirect to /admin",
    ], S)
    elements.append(p(
        "The shared <b>_release_reservation()</b> helper ensures billing logic is identical "
        "whether a user checks out themselves or an admin forces a release.", S["note"]
    ))

    # 6.9
    elements += sub("6.9  Admin — Lot Management (Add / Edit / Delete)")
    elements += code_block([
        "POST /admin/lots/add",
        "  → Create ParkingLot object from form data",
        "  → db.session.flush()     ← assigns new lot.id BEFORE commit",
        "  → _make_spots(lot.id, total_spots)  ← auto-generates all spot records",
        "  → db.session.commit()",
        "",
        "POST /admin/lots/edit/<lot_id>",
        "  → Fetch lot, update fields, commit",
        "",
        "POST /admin/lots/delete/<lot_id>",
        "  → Delete all Spots for this lot (manual cascade)",
        "  → Delete all Reservations for this lot",
        "  → Delete the lot itself",
        "  → db.session.commit()",
    ], S)

    # 6.10
    elements += sub("6.10  Reports &amp; Analytics")
    elements += code_block([
        "GET /admin/reports",
        "  → Query 1: SUM(cost) WHERE status='completed'  → total_revenue",
        "  → Query 2: COUNT(*) all reservations           → total_res_count",
        "  → Query 3: JOIN User + Reservation",
        "             GROUP BY user_id",
        "             ORDER BY SUM(cost) DESC LIMIT 5     → top 5 spenders",
        "  → Query 4: GROUP BY DATE(check_in)",
        "             for last 7 days                     → daily revenue table",
        "  → All are single SQL queries via SQLAlchemy func.sum(), func.count()",
    ], S)

    # 6.11
    elements += sub("6.11  CSV Export Flow")
    elements += code_block([
        "GET /history/csv  (user)   OR   GET /admin/reports/csv  (admin)",
        "  → Fetch reservations from DB",
        "  → Create in-memory io.StringIO() buffer  (no temp file on disk)",
        "  → Write UTF-8 BOM (\\ufeff) — makes Excel open ₹ symbol correctly",
        "  → Write header row, then one data row per reservation",
        "  → Return Response(",
        "        mimetype='text/csv',",
        "        Content-Disposition: attachment; filename=parkvault-history.csv",
        "    )",
        "  → Browser automatically triggers file download",
    ], S)

    # ── Section 7 ─────────────────────────────────────────────────────────────
    elements += h("7. Authentication &amp; Security Layers")
    elements.append(p("There are <b>three levels of access control</b> in ParkVault:"))
    elements += data_table(
        ["Level", "Mechanism", "Applied To", "Action if Failed"],
        [
            ["1 — Session check", "@login_required decorator", "ALL user + admin routes", "Redirect to login page (/)"],
            ["2 — Admin check", "@admin_required decorator", "All /admin/* routes", "Redirect to login page"],
            ["3 — Ownership check", "Logic in route body", "Release, Edit, Delete", "Silent redirect / flash error"],
        ],
        S, col_widths=[3.5*cm, 5*cm, 5.5*cm, 4.5*cm]
    )
    elements.append(p("<b>Additional security measures:</b>", BL))
    for item in [
        "Passwords hashed with bcrypt (salted one-way hash) — never stored as plain text",
        "Server-side check_in timestamps — billing cannot be manipulated via client clock",
        "Double-check spot availability at /reserve — prevents race condition double-booking",
        "Admin cannot delete their own account or demote their own role",
        "Flask SECRET_KEY signs session cookies — prevents forged sessions",
    ]:
        elements.append(p(f"• {item}", BU))

    # ── Section 8 ─────────────────────────────────────────────────────────────
    elements += h("8. Theme System — Dark / Light Mode")
    elements.append(p(
        "The entire UI theming is controlled by a single HTML attribute on the root element:"
    ))
    elements += code_block([
        '<html data-theme="dark">   ← switches to data-theme="light" on toggle',
    ], S)
    elements.append(p(
        "All colours are defined as <b>CSS Custom Properties (variables)</b>:"
    ))
    elements += code_block([
        ":root {",
        "  --glass-bg:   rgba(255,255,255,0.06);",
        "  --text-primary: #e8f0ff;",
        "}",
        "[data-theme='light'] {",
        "  --glass-bg:   rgba(255,255,255,0.72);",
        "  --text-primary: #0d1527;",
        "}",
    ], S)
    elements.append(p(
        "When the user clicks the theme toggle button, JavaScript updates the attribute and "
        "saves the preference to <b>localStorage</b> — so it persists across page loads and "
        "browser sessions. No server round-trip is needed; it is entirely client-side."
    ))

    # ── Section 9 ─────────────────────────────────────────────────────────────
    elements += h("9. Data Flow Diagram")
    elements += code_block([
        "┌──────────────────────────────────────────────────────────┐",
        "│                       BROWSER                           │",
        "│   HTML Page + CSS + JavaScript                          │",
        "│   - Jinja2 variables already embedded in the HTML       │",
        "│   - JS only used for: spot grid, modals, theme toggle   │",
        "└─────────────────────────┬────────────────────────────────┘",
        "                          │  HTTP GET or POST",
        "┌─────────────────────────▼────────────────────────────────┐",
        "│                  Flask  (run.py)                        │",
        "│                                                          │",
        "│  Route Handler                                           │",
        "│    ├─ Decorator checks (login_required, admin_required)  │",
        "│    ├─ Read / Write via SQLAlchemy ORM                   │",
        "│    └─ render_template() → Jinja2 fills in HTML          │",
        "└─────────────────────────┬────────────────────────────────┘",
        "                          │  SQL (SELECT / INSERT / UPDATE)",
        "┌─────────────────────────▼────────────────────────────────┐",
        "│            SQLite Database  (parkvault.db)               │",
        "│                                                          │",
        "│   user  ──< reservation >──  parking_lot                 │",
        "│                                  │                       │",
        "│                                spot                      │",
        "└──────────────────────────────────────────────────────────┘",
    ], S)

    # ── Section 10 ────────────────────────────────────────────────────────────
    elements += h("10. Key Design Decisions")
    elements += data_table(
        ["Design Decision", "Reason / Justification"],
        [
            ["SQLite instead of MySQL / PostgreSQL",
             "Zero-configuration, single file database. Ideal for academic/prototype project — no server setup needed."],
            ["Server-side rendering with Jinja2",
             "Simpler than React/Vue/Angular. No separate frontend build pipeline. Entire app runs from one Python file."],
            ["bcrypt for password hashing",
             "Industry-standard algorithm. Automatically applies salting, preventing rainbow table and brute-force attacks."],
            ["Server datetime.now() for billing",
             "Prevents client-side clock manipulation. A user cannot set their phone to an earlier time to get a cheaper bill."],
            ["Shared _release_reservation() helper",
             "DRY (Don't Repeat Yourself) principle — single source of truth for billing logic used by both user checkout and admin force-release."],
            ["db.session.flush() before _make_spots()",
             "Assigns the new lot.id within the transaction before commit. Required because Spot records need the FK lot_id immediately."],
            ["UTF-8 BOM in CSV export",
             "Ensures Microsoft Excel opens Indian Rupee symbol (₹) and special characters correctly on Windows machines."],
            ["CSS :has() for overflow scoping",
             "Only table-containing glass panels get horizontal scroll. Form panels and stat card panels are unaffected — no unnecessary scrollbars."],
            ["@admin_required as a separate decorator",
             "Keeps route functions clean. Any route can be protected by stacking @login_required + @admin_required without repeating the check logic."],
            ["Per-second billing (not per-hour rounding)",
             "Fairer to users. Cost calculated as (total_seconds / 3600) × rate, so a 47-minute session is not rounded up to a full hour."],
        ],
        S, col_widths=[6*cm, 12.5*cm]
    )

    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=10))
    elements.append(Paragraph(
        "ParkVault — MCA Final Year Project &nbsp;|&nbsp; Smart Parking Management System",
        ParagraphStyle("footer", fontName="Helvetica", fontSize=9,
                       textColor=MUTED, alignment=TA_CENTER)
    ))

    return elements


# ── Page template with header/footer ─────────────────────────────────────────
def make_page_template(canvas, doc):
    canvas.saveState()
    W, H = A4

    # Top accent bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, H - 28, W, 28, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, H - 30, W, 2, fill=1, stroke=0)

    # Header text
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(2*cm, H - 19, "ParkVault — Smart Parking Management System")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(W - 2*cm, H - 19, "MCA Final Year Project Documentation")

    # Bottom footer
    canvas.setFillColor(RULE_COLOR)
    canvas.rect(0, 0, W, 22, fill=1, stroke=0)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2*cm, 7, "Confidential — For Academic Evaluation Only")
    canvas.drawRightString(W - 2*cm, 7, f"Page {doc.page}")

    canvas.restoreState()


# ── Build the PDF ─────────────────────────────────────────────────────────────
def generate():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2.2*cm,
        bottomMargin=1.8*cm,
        title="ParkVault — Project Documentation",
        author="MCA Final Year Project",
        subject="Smart Parking Management System",
    )

    styles = build_styles()
    story  = []
    story += cover_page(styles)
    story += toc(styles)
    story += build_content(styles)

    doc.build(story, onFirstPage=make_page_template, onLaterPages=make_page_template)
    print(f"✅  PDF generated: {OUTPUT}")


if __name__ == "__main__":
    generate()
