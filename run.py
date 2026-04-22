from flask import (Flask, render_template, request, redirect,
                   url_for, flash, Response, jsonify)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from functools import wraps
from models import db, User, ParkingLot, Spot, Reservation
from datetime import datetime, timedelta
from sqlalchemy import func, text, inspect
from apscheduler.schedulers.background import BackgroundScheduler
import atexit, os
import time
import csv, io

# ── App setup ─────────────────────────────────────────────────────────────────

app = Flask(__name__, template_folder='.', static_url_path='', static_folder='.')
app.config['SECRET_KEY'] = 'parkvault-dev-secret-change-in-prod'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parkvault.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Mail config  (set these env vars or edit directly for testing) ─────────────
#   MAIL_USERNAME  → your Gmail address  e.g. yourapp@gmail.com
#   MAIL_PASSWORD  → Gmail App Password  (not your login password)
#                    Generate at: myaccount.google.com → Security → App Passwords
app.config['MAIL_SERVER']         = os.environ.get('MAIL_SERVER',   'smtp.gmail.com')
app.config['MAIL_PORT']           = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS']        = True
app.config['MAIL_USE_SSL']        = False
app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = (
    'ParkVault',
    os.environ.get('MAIL_USERNAME') or 'noreply@parkvault.com'
)
# Silently suppress sending when credentials are not configured
app.config['MAIL_SUPPRESS_SEND']  = not bool(os.environ.get('MAIL_USERNAME'))

db.init_app(app)
bcrypt = Bcrypt(app)
mail   = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))

# ── Decorators ────────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Seed data ─────────────────────────────────────────────────────────────────

SEED_LOTS = [
    dict(name='Sarojini Nagar Hub',     address='Sarojini Nagar, Jaipur',  pin_code='302005', lot_type='open',        total_spots=40, rate_per_hour=30.0),
    dict(name='Civil Lines Parking',    address='Civil Lines, Jaipur',     pin_code='302006', lot_type='covered',     total_spots=60, rate_per_hour=25.0),
    dict(name='Pink City Mall Lot',     address='MI Road, Jaipur',         pin_code='302001', lot_type='multi-level', total_spots=80, rate_per_hour=40.0),
    dict(name='Railway Station Lot',    address='Jaipur Junction',         pin_code='302006', lot_type='open',        total_spots=50, rate_per_hour=20.0),
    dict(name='Vaishali Nagar Parking', address='Vaishali Nagar, Jaipur',  pin_code='302021', lot_type='open',        total_spots=45, rate_per_hour=20.0),
    dict(name='Mansarovar Complex',     address='Mansarovar, Jaipur',      pin_code='302020', lot_type='covered',     total_spots=35, rate_per_hour=35.0, status='inactive'),
]

def _make_spots(lot_id, total):
    for i in range(1, total + 1):
        row = chr(ord('A') + (i - 1) // 10)
        num = ((i - 1) % 10) + 1
        db.session.add(Spot(lot_id=lot_id, spot_number=f"{row}-{num:02d}"))

def _make_spots_multilevel(lot_id, level_spots):
    """Create spots for a multi-level lot.
    level_spots: list where level_spots[i] = number of spots on level i+1.
    Naming convention: L1-A-01, L1-A-02 … L1-B-01 … L2-A-01 …
    """
    for lvl_idx, count in enumerate(level_spots):
        prefix = f'L{lvl_idx + 1}'
        for i in range(1, count + 1):
            row = chr(ord('A') + (i - 1) // 10)
            num = ((i - 1) % 10) + 1
            db.session.add(Spot(lot_id=lot_id, spot_number=f"{prefix}-{row}-{num:02d}"))

def seed_db():
    if User.query.count() > 0:
        return

    # ── Admin accounts ────────────────────────────────────────────────────────
    admins = [
        dict(first_name='Super',  last_name='Admin',   email='admin@parkvault.com',
             phone='+91 98000 00001', vehicle='ADMIN-00', is_admin=True,  password='admin123'),
        dict(first_name='Xavier', last_name='Ops',     email='xavier@parkvault.com',
             phone='+91 98000 00002', vehicle='ADMIN-01', is_admin=True,  password='xavier123'),
    ]

    # ── Dummy regular users (no bookings) ─────────────────────────────────────
    users = [
        dict(first_name='Aarav',   last_name='Sharma',   email='aarav@example.com',
             phone='+91 98111 11111', vehicle='RJ14 AB 1234', is_admin=False, password='user123'),
        dict(first_name='Priya',   last_name='Mehta',    email='priya@example.com',
             phone='+91 98222 22222', vehicle='RJ14 CD 5678', is_admin=False, password='user123'),
        dict(first_name='Rohan',   last_name='Verma',    email='rohan@example.com',
             phone='+91 98333 33333', vehicle='RJ14 EF 9012', is_admin=False, password='user123'),
        dict(first_name='Sneha',   last_name='Gupta',    email='sneha@example.com',
             phone='+91 98444 44444', vehicle='RJ14 GH 3456', is_admin=False, password='user123'),
        dict(first_name='Karan',   last_name='Singh',    email='karan@example.com',
             phone='+91 98555 55555', vehicle='RJ14 IJ 7890', is_admin=False, password='user123'),
        dict(first_name='Anjali',  last_name='Patel',    email='anjali@example.com',
             phone='+91 98666 66666', vehicle='RJ14 KL 2345', is_admin=False, password='user123'),
        dict(first_name='Vikram',  last_name='Rao',      email='vikram@example.com',
             phone='+91 98777 77777', vehicle='RJ14 MN 6789', is_admin=False, password='user123'),
        dict(first_name='Neha',    last_name='Joshi',    email='neha@example.com',
             phone='+91 98888 88888', vehicle='RJ14 OP 0123', is_admin=False, password='user123'),
    ]

    for u_data in admins + users:
        pw = u_data.pop('password')
        u_data['password_hash'] = bcrypt.generate_password_hash(pw).decode()
        db.session.add(User(**u_data))

    # ── Parking lots & spots ──────────────────────────────────────────────────
    for ld in SEED_LOTS:
        lot = ParkingLot(**ld)
        db.session.add(lot)
        db.session.flush()
        _make_spots(lot.id, ld['total_spots'])

    db.session.commit()

# ── Helper ────────────────────────────────────────────────────────────────────

def _report_filters(date_from_str, date_to_str, sel_user_ids, sel_lot_ids):
    """Return a list of SQLAlchemy filter conditions from report query params."""
    conds = []
    if date_from_str:
        try:
            conds.append(Reservation.check_in >= datetime.strptime(date_from_str, '%Y-%m-%d'))
        except ValueError:
            pass
    if date_to_str:
        try:
            dt_to = datetime.strptime(date_to_str, '%Y-%m-%d') + timedelta(days=1)
            conds.append(Reservation.check_in < dt_to)
        except ValueError:
            pass
    if sel_user_ids:
        conds.append(Reservation.user_id.in_(sel_user_ids))
    if sel_lot_ids:
        conds.append(Reservation.lot_id.in_(sel_lot_ids))
    return conds

def _release_reservation(res):
    """Shared logic for user self-release and admin force-release."""
    res.check_out = datetime.now()
    secs = (res.check_out - res.check_in).total_seconds()
    res.cost = round((secs / 3600) * res.lot.rate_per_hour, 2)
    res.status = 'completed'
    spot = Spot.query.filter_by(lot_id=res.lot_id, spot_number=res.spot_number).first()
    if spot:
        spot.is_occupied = False
    # Mark user as no longer parked if no other active reservations
    still_parked = Reservation.query.filter_by(user_id=res.user_id, status='active').count()
    if not still_parked:
        res.user.status = 'active'
    db.session.commit()
    send_release_receipt(res)               # ← receipt email

# ── Email helpers ─────────────────────────────────────────────────────────────

def _safe_send(msg):
    """Send an email. Silently skips if mail is not configured or sending fails."""
    if not app.config.get('MAIL_USERNAME'):
        app.logger.info('[Mail] Not configured — skipping send to %s', msg.recipients)
        return
    try:
        mail.send(msg)
    except Exception as exc:
        app.logger.warning('[Mail] Failed sending to %s: %s', msg.recipients, exc)


def _email_wrap(subtitle, body_html):
    """Wrap body HTML in a consistent dark-themed email shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background:#0d1117;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0d1117;">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="580" cellpadding="0" cellspacing="0" border="0"
             style="background:#161b27;border-radius:16px;border:1px solid #1e2840;overflow:hidden;max-width:580px;">
        <!-- Header -->
        <tr><td style="background:linear-gradient(135deg,#1a2456 0%,#2a1850 100%);padding:28px 36px;">
          <p style="margin:0;font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.3px;">&#x1F17F;&#xFE0F; ParkVault</p>
          <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,0.55);">{subtitle}</p>
        </td></tr>
        <!-- Body -->
        <tr><td style="padding:32px 36px;color:#cbd5e1;font-size:14px;line-height:1.7;">
          {body_html}
        </td></tr>
        <!-- Footer -->
        <tr><td style="padding:18px 36px;border-top:1px solid #1e2840;">
          <p style="margin:0;font-size:11px;color:rgba(255,255,255,0.25);">
            ParkVault &mdash; Smart Parking Management &nbsp;|&nbsp; This is an automated message, do not reply.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _info_row(label, value, accent=False):
    val_style = 'font-weight:700;color:#4facfe;' if accent else 'font-weight:600;color:#e2e8f0;'
    return f"""<tr>
      <td style="padding:8px 0;font-size:13px;color:rgba(255,255,255,0.5);width:140px;">{label}</td>
      <td style="padding:8px 0;font-size:13px;{val_style}">{value}</td>
    </tr>"""


# 1. Booking Confirmation ──────────────────────────────────────────────────────

def send_booking_confirmation(res):
    """Sent to the user immediately after they reserve a spot."""
    user = res.user
    body = f"""
      <p style="margin:0 0 20px;font-size:16px;font-weight:600;color:#fff;">
        Hi {user.first_name}, your spot is confirmed! &#x1F389;
      </p>
      <table cellpadding="0" cellspacing="0" border="0" width="100%"
             style="background:#0d1117;border-radius:12px;padding:20px 24px;margin-bottom:24px;">
        {_info_row('Parking Lot',  res.lot.name)}
        {_info_row('Spot Number',  res.spot_number)}
        {_info_row('Check-in',     res.check_in.strftime('%d %b %Y, %I:%M %p'))}
        {_info_row('Rate',         f'&#8377;{res.lot.rate_per_hour:.0f} / hour')}
      </table>
      <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.45);">
        Head to the lot and your spot is waiting. Release it from your dashboard when done.
      </p>
    """
    msg = Message(
        subject=f'Booking Confirmed – Spot {res.spot_number} at {res.lot.name}',
        recipients=[user.email],
        html=_email_wrap('Booking Confirmation', body)
    )
    _safe_send(msg)


# 2. Spot Release Receipt ──────────────────────────────────────────────────────

def send_release_receipt(res):
    """Sent to the user after they (or admin) release a spot."""
    user = res.user
    secs     = int((res.check_out - res.check_in).total_seconds())
    duration = f"{secs // 3600}h {(secs % 3600) // 60}m"
    body = f"""
      <p style="margin:0 0 20px;font-size:16px;font-weight:600;color:#fff;">
        Thanks for using ParkVault, {user.first_name}! Here&rsquo;s your receipt.
      </p>
      <table cellpadding="0" cellspacing="0" border="0" width="100%"
             style="background:#0d1117;border-radius:12px;padding:20px 24px;margin-bottom:24px;">
        {_info_row('Parking Lot',  res.lot.name)}
        {_info_row('Spot Number',  res.spot_number)}
        {_info_row('Check-in',     res.check_in.strftime('%d %b %Y, %I:%M %p'))}
        {_info_row('Check-out',    res.check_out.strftime('%d %b %Y, %I:%M %p'))}
        {_info_row('Duration',     duration)}
        {_info_row('Total Cost',   f'&#8377;{res.cost:.2f}', accent=True)}
      </table>
      <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.45);">
        We hope you had a smooth experience. See you next time!
      </p>
    """
    msg = Message(
        subject=f'Parking Receipt – \u20b9{res.cost:.2f} | {res.lot.name}',
        recipients=[user.email],
        html=_email_wrap('Parking Receipt', body)
    )
    _safe_send(msg)


# 3. Long-stay Reminder ───────────────────────────────────────────────────────

def send_long_stay_alerts():
    """Scheduled hourly. Alerts users who have been parked for 2+ hours."""
    cutoff = datetime.now() - timedelta(hours=2)
    long_res = (Reservation.query
                .filter_by(status='active')
                .filter(Reservation.check_in <= cutoff)
                .all())
    for res in long_res:
        secs      = int((datetime.now() - res.check_in).total_seconds())
        duration  = f"{secs // 3600}h {(secs % 3600) // 60}m"
        est_cost  = round((secs / 3600) * res.lot.rate_per_hour, 2)
        body = f"""
          <p style="margin:0 0 20px;font-size:16px;font-weight:600;color:#fff;">
            &#x23F0; Heads up, {res.user.first_name}!
          </p>
          <p style="margin:0 0 20px;font-size:14px;color:rgba(255,255,255,0.7);">
            Your vehicle has been parked at <strong style="color:#fff;">{res.lot.name}</strong>
            for <strong style="color:#4facfe;">{duration}</strong>.
          </p>
          <table cellpadding="0" cellspacing="0" border="0" width="100%"
                 style="background:#0d1117;border-radius:12px;padding:20px 24px;margin-bottom:24px;">
            {_info_row('Spot',         res.spot_number)}
            {_info_row('Parked Since', res.check_in.strftime('%I:%M %p'))}
            {_info_row('Duration',     duration)}
            {_info_row('Est. Cost',    f'&#8377;{est_cost:.2f}', accent=True)}
          </table>
          <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.45);">
            Log in to your dashboard to release the spot when you&rsquo;re done.
          </p>
        """
        msg = Message(
            subject=f'\u23F0 Parking Reminder – {res.lot.name} ({duration})',
            recipients=[res.user.email],
            html=_email_wrap('Long Stay Reminder', body)
        )
        _safe_send(msg)


# 4. Daily Admin Summary ───────────────────────────────────────────────────────

def send_daily_admin_summary():
    """Scheduled daily at 8 AM. Sends a summary of yesterday's activity to all admins."""
    yesterday_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    yesterday_end   = yesterday_start + timedelta(days=1)

    sessions  = (Reservation.query
                 .filter(Reservation.check_in >= yesterday_start,
                         Reservation.check_in  < yesterday_end)
                 .count())
    completed = (Reservation.query
                 .filter(Reservation.status == 'completed',
                         Reservation.check_in >= yesterday_start,
                         Reservation.check_in  < yesterday_end)
                 .count())
    revenue   = (db.session.query(func.sum(Reservation.cost))
                 .filter(Reservation.status == 'completed',
                         Reservation.check_in >= yesterday_start,
                         Reservation.check_in  < yesterday_end)
                 .scalar() or 0)
    currently_active = Reservation.query.filter_by(status='active').count()

    date_label = yesterday_start.strftime('%d %b %Y')
    body = f"""
      <p style="margin:0 0 20px;font-size:16px;font-weight:600;color:#fff;">
        Daily Summary for {date_label}
      </p>
      <table cellpadding="0" cellspacing="0" border="0" width="100%"
             style="background:#0d1117;border-radius:12px;padding:20px 24px;margin-bottom:24px;">
        {_info_row('Total Sessions',     sessions)}
        {_info_row('Completed',          completed)}
        {_info_row('Revenue',            f'&#8377;{revenue:.2f}', accent=True)}
        {_info_row('Currently Active',   currently_active)}
      </table>
      <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.45);">
        View the full report at your admin panel &rarr; Reports &amp; Revenue.
      </p>
    """
    admins = User.query.filter_by(is_admin=True).all()
    for admin in admins:
        msg = Message(
            subject=f'ParkVault Daily Report – {date_label}',
            recipients=[admin.email],
            html=_email_wrap('Daily Admin Summary', body)
        )
        _safe_send(msg)


# 5. Monthly Report Email ─────────────────────────────────────────────────────

def send_monthly_report_email():
    """Triggered on-demand by admin. Sends this month's full stats to all admins."""
    now             = datetime.now()
    month_start     = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_label     = now.strftime('%B %Y')

    sessions  = (Reservation.query
                 .filter(Reservation.check_in >= month_start)
                 .count())
    completed = (Reservation.query
                 .filter(Reservation.status == 'completed',
                         Reservation.check_in >= month_start)
                 .count())
    revenue   = (db.session.query(func.sum(Reservation.cost))
                 .filter(Reservation.status == 'completed',
                         Reservation.check_in >= month_start)
                 .scalar() or 0)
    unique_u  = (db.session.query(func.count(func.distinct(Reservation.user_id)))
                 .filter(Reservation.check_in >= month_start)
                 .scalar() or 0)
    avg_cost  = round(revenue / completed, 2) if completed else 0

    top_users = (db.session.query(User, func.sum(Reservation.cost).label('spent'))
                 .join(Reservation, Reservation.user_id == User.id)
                 .filter(Reservation.status == 'completed',
                         Reservation.check_in >= month_start)
                 .group_by(User.id)
                 .order_by(func.sum(Reservation.cost).desc())
                 .limit(5).all())
    top_rows = ''.join(
        f'<tr><td style="padding:6px 0;font-size:13px;color:#e2e8f0;">{u.name}</td>'
        f'<td style="padding:6px 0;font-size:13px;font-weight:700;color:#4facfe;text-align:right;">&#8377;{s:.2f}</td></tr>'
        for u, s in top_users
    ) or '<tr><td colspan="2" style="color:rgba(255,255,255,0.3);font-size:13px;">No data</td></tr>'

    body = f"""
      <p style="margin:0 0 20px;font-size:16px;font-weight:600;color:#fff;">
        Monthly Report &mdash; {month_label}
      </p>
      <table cellpadding="0" cellspacing="0" border="0" width="100%"
             style="background:#0d1117;border-radius:12px;padding:20px 24px;margin-bottom:24px;">
        {_info_row('Total Sessions',  sessions)}
        {_info_row('Completed',       completed)}
        {_info_row('Total Revenue',   f'&#8377;{revenue:.2f}', accent=True)}
        {_info_row('Unique Users',    unique_u)}
        {_info_row('Avg Cost/Session',f'&#8377;{avg_cost:.2f}')}
      </table>
      <p style="margin:0 0 12px;font-size:13px;font-weight:600;color:#fff;">Top Users by Spend</p>
      <table cellpadding="0" cellspacing="0" border="0" width="100%"
             style="background:#0d1117;border-radius:12px;padding:16px 24px;margin-bottom:24px;">
        {top_rows}
      </table>
      <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.45);">
        For detailed breakdowns and CSV exports, visit the admin Reports &amp; Revenue page.
      </p>
    """
    admins = User.query.filter_by(is_admin=True).all()
    sent   = 0
    for admin in admins:
        msg = Message(
            subject=f'ParkVault Monthly Report – {month_label}',
            recipients=[admin.email],
            html=_email_wrap(f'Monthly Report · {month_label}', body)
        )
        _safe_send(msg)
        sent += 1
    return sent


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route('/')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard') if current_user.is_admin else url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def do_login():
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        login_user(user)
        return redirect(url_for('admin_dashboard') if user.is_admin else url_for('user_dashboard'))
    flash('Invalid email or password.')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fname   = request.form.get('fname', '').strip()
        lname   = request.form.get('lname', '').strip()
        email   = request.form.get('email', '').strip().lower()
        phone   = request.form.get('phone', '').strip()
        vehicle = request.form.get('vehicle', '').strip()
        pw      = request.form.get('pass', '')
        cpw     = request.form.get('cpass', '')
        if pw != cpw:
            flash('Passwords do not match.')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.')
            return render_template('register.html')
        user = User(
            first_name    = fname,
            last_name     = lname,
            email         = email,
            phone         = phone,
            vehicle       = vehicle,
            password_hash = bcrypt.generate_password_hash(pw).decode()
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('user_dashboard'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ── User routes ───────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def user_dashboard():
    active_res  = Reservation.query.filter_by(user_id=current_user.id, status='active').first()
    recent_res  = (Reservation.query
                   .filter_by(user_id=current_user.id)
                   .order_by(Reservation.check_in.desc())
                   .limit(4).all())
    total_res   = Reservation.query.filter_by(user_id=current_user.id).count()
    total_spent = (db.session.query(func.sum(Reservation.cost))
                   .filter_by(user_id=current_user.id, status='completed')
                   .scalar() or 0)
    return render_template('user-dashboard.html',
        active_res=active_res, recent_res=recent_res,
        total_res=total_res, total_spent=total_spent,
        now=datetime.now())

@app.route('/search')
@login_required
def search_parking():
    q     = request.args.get('q', '').strip()
    type_ = request.args.get('type', '').strip()
    query = ParkingLot.query.filter_by(status='active')
    if q:
        query = query.filter(
            db.or_(ParkingLot.name.ilike(f'%{q}%'),
                   ParkingLot.pin_code.contains(q),
                   ParkingLot.address.ilike(f'%{q}%')))
    if type_:
        query = query.filter(ParkingLot.lot_type == type_)
    lots = query.all()
    for lot in lots:
        lot.free_count = Spot.query.filter_by(lot_id=lot.id, is_occupied=False).count()
    return render_template('search-parking.html', lots=lots, q=q, type_=type_)

@app.route('/spots')
@login_required
def spot_selection():
    lot_id = request.args.get('lot_id', type=int)
    if not lot_id:
        return redirect(url_for('search_parking'))
    lot = db.get_or_404(ParkingLot, lot_id)
    spots = Spot.query.filter_by(lot_id=lot_id).order_by(Spot.spot_number).all()
    free_count = sum(1 for s in spots if not s.is_occupied)
    return render_template('spot-selection.html', lot=lot, spots=spots, free_count=free_count)

@app.route('/reserve', methods=['POST'])
@login_required
def reserve():
    lot_id      = request.form.get('lot_id', type=int)
    spot_number = request.form.get('spot_number', '').strip()
    lot  = db.get_or_404(ParkingLot, lot_id)
    spot = Spot.query.filter_by(lot_id=lot_id, spot_number=spot_number, is_occupied=False).first()
    if not spot:
        flash('That spot is no longer available. Please choose another.')
        return redirect(url_for('spot_selection', lot_id=lot_id))
    # Always use server UTC time — avoids timezone mismatch with JS local time
    check_in = datetime.now()
    res = Reservation(
        user_id     = current_user.id,
        lot_id      = lot_id,
        spot_number = spot_number,
        check_in    = check_in,
        status      = 'active'
    )
    spot.is_occupied    = True
    current_user.status = 'parked'
    db.session.add(res)
    db.session.commit()
    send_booking_confirmation(res)          # ← confirmation email
    return redirect(url_for('user_dashboard'))

@app.route('/release', methods=['POST'])
@login_required
def release():
    res_id = request.form.get('res_id', type=int)
    res = db.get_or_404(Reservation, res_id)
    if res.user_id != current_user.id:
        return redirect(url_for('user_dashboard'))
    _release_reservation(res)
    return redirect(url_for('user_dashboard'))

@app.route('/history')
@login_required
def reservation_history():
    all_res = (Reservation.query
               .filter_by(user_id=current_user.id)
               .order_by(Reservation.check_in.desc())
               .all())
    total_spent     = sum(r.cost for r in all_res if r.cost)
    completed_count = sum(1 for r in all_res if r.status == 'completed')
    return render_template('reservation-history.html',
        reservations=all_res,
        total_spent=total_spent,
        completed_count=completed_count,
        now=datetime.now())

@app.route('/history/csv')
@login_required
def history_csv():
    all_res = (Reservation.query
               .filter_by(user_id=current_user.id)
               .order_by(Reservation.check_in.desc()).all())
    out = io.StringIO()
    out.write('\ufeff')          # UTF-8 BOM — makes Excel open correctly
    w = csv.writer(out)
    w.writerow(['#', 'Lot', 'Spot', 'Check In', 'Check Out',
                'Duration', 'Cost (INR)', 'Status'])
    for sno, r in enumerate(all_res, start=1):
        if r.check_out and r.check_in:
            secs     = int((r.check_out - r.check_in).total_seconds())
            duration = f"{secs//3600}h {(secs%3600)//60}m"
        else:
            duration = 'Ongoing' if r.status == 'active' else '-'
        w.writerow([
            sno,
            r.lot.name,
            r.spot_number,
            r.check_in.strftime('%d %b %Y  %I:%M %p'),
            r.check_out.strftime('%d %b %Y  %I:%M %p') if r.check_out else '-',
            duration,
            f'{r.cost:.2f}' if r.cost else '0.00',
            r.status.capitalize()
        ])
    return Response(
        out.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=parkvault-history.csv'}
    )

# ── Admin routes ──────────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    lots_count  = ParkingLot.query.count()
    users_count = User.query.filter_by(is_admin=False).count()
    total_spots = db.session.query(func.sum(ParkingLot.total_spots)).scalar() or 0
    avail_spots = Spot.query.filter_by(is_occupied=False).count()
    active_res  = (Reservation.query.filter_by(status='active')
                   .order_by(Reservation.check_in).all())
    return render_template('admin-dashboard.html',
        lots_count=lots_count, users_count=users_count,
        total_spots=total_spots, available_spots=avail_spots,
        active_reservations=active_res, now=datetime.now())

@app.route('/admin/lots')
@login_required
@admin_required
def admin_lots():
    lots = ParkingLot.query.all()
    for lot in lots:
        lot.free_count = Spot.query.filter_by(lot_id=lot.id, is_occupied=False).count()
    return render_template('admin-lots.html', lots=lots)

@app.route('/admin/lots/add', methods=['POST'])
@login_required
@admin_required
def admin_lots_add():
    lot_type = request.form.get('lot_type', 'open')

    if lot_type == 'multi-level':
        levels      = int(request.form.get('levels', 0) or 0)
        level_spots = []
        for i in range(1, levels + 1):
            n = int(request.form.get(f'spots_level_{i}', 0) or 0)
            level_spots.append(n)
        total = sum(level_spots)
        if levels < 1 or total < 1:
            flash('Please specify at least 1 level with at least 1 spot per level.', 'error')
            return redirect(url_for('admin_lots'))
    else:
        total       = int(request.form.get('total_spots', 0) or 0)
        level_spots = None

    lot = ParkingLot(
        name          = request.form.get('name', '').strip(),
        lot_type      = lot_type,
        address       = request.form.get('address', '').strip(),
        pin_code      = request.form.get('pin_code', '').strip(),
        total_spots   = total,
        rate_per_hour = float(request.form.get('rate_per_hour', 0) or 0),
        status        = request.form.get('status', 'active')
    )
    db.session.add(lot)
    db.session.flush()

    if lot_type == 'multi-level' and level_spots:
        _make_spots_multilevel(lot.id, level_spots)
    else:
        _make_spots(lot.id, total)

    db.session.commit()
    return redirect(url_for('admin_lots'))

@app.route('/admin/lots/edit/<int:lot_id>', methods=['POST'])
@login_required
@admin_required
def admin_lots_edit(lot_id):
    lot = db.get_or_404(ParkingLot, lot_id)
    lot.name          = request.form.get('name', lot.name).strip()
    lot.lot_type      = request.form.get('lot_type', lot.lot_type)
    lot.address       = request.form.get('address', lot.address).strip()
    lot.pin_code      = request.form.get('pin_code', lot.pin_code).strip()
    lot.rate_per_hour = float(request.form.get('rate_per_hour', lot.rate_per_hour))
    lot.status        = request.form.get('status', lot.status)
    db.session.commit()
    return redirect(url_for('admin_lots'))

@app.route('/admin/lots/delete/<int:lot_id>', methods=['POST'])
@login_required
@admin_required
def admin_lots_delete(lot_id):
    lot = db.get_or_404(ParkingLot, lot_id)
    Spot.query.filter_by(lot_id=lot_id).delete()
    Reservation.query.filter_by(lot_id=lot_id).delete()
    db.session.delete(lot)
    db.session.commit()
    return redirect(url_for('admin_lots'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    q    = request.args.get('q', '').strip()
    base_q = User.query.filter_by(is_admin=False)
    if q:
        base_q = base_q.filter(
            db.or_(User.first_name.ilike(f'%{q}%'),
                   User.last_name.ilike(f'%{q}%'),
                   User.email.ilike(f'%{q}%'),
                   User.vehicle.ilike(f'%{q}%')))
    users_page = base_q.order_by(User.joined.desc()).paginate(page=page, per_page=10, error_out=False)
    # Annotate each user with aggregated stats, return as list of (User, count, spent) tuples
    rows = []
    for u in users_page.items:
        booking_count = Reservation.query.filter_by(user_id=u.id).count()
        total_spent   = (db.session.query(func.sum(Reservation.cost))
                         .filter(Reservation.user_id == u.id,
                                 Reservation.status == 'completed')
                         .scalar() or 0)
        rows.append((u, booking_count, total_spent))
    # Replace items with annotated tuples using a simple wrapper
    users_page.items = rows

    # Fetch admin users separately for the Admin Accounts section
    admin_users_raw  = User.query.filter_by(is_admin=True).order_by(User.joined.desc()).all()
    admin_users_list = []
    for u in admin_users_raw:
        bc = Reservation.query.filter_by(user_id=u.id).count()
        ts = (db.session.query(func.sum(Reservation.cost))
              .filter(Reservation.user_id == u.id,
                      Reservation.status == 'completed')
              .scalar() or 0)
        admin_users_list.append((u, bc, ts))

    all_users   = User.query.filter_by(is_admin=False).all()
    total       = User.query.count()
    admin_count = User.query.filter_by(is_admin=True).count()
    parked      = sum(1 for u in all_users if u.status == 'parked')
    suspended   = sum(1 for u in all_users if u.status == 'suspended')
    return render_template('admin-users.html',
        users_page=users_page, total=total,
        admin_count=admin_count, parked=parked, suspended=suspended,
        q=q, admin_users_list=admin_users_list)

@app.route('/admin/users/suspend/<int:uid>', methods=['POST'])
@login_required
@admin_required
def admin_users_suspend(uid):
    u = db.get_or_404(User, uid)
    u.status = 'active' if u.status == 'suspended' else 'suspended'
    db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    date_from_str = request.args.get('date_from', '').strip()
    date_to_str   = request.args.get('date_to', '').strip()
    sel_user_ids  = request.args.getlist('user_ids', type=int)
    sel_lot_ids   = request.args.getlist('lot_ids', type=int)
    is_filtered   = bool(date_from_str or date_to_str or sel_user_ids or sel_lot_ids)

    conds = _report_filters(date_from_str, date_to_str, sel_user_ids, sel_lot_ids)

    total_revenue = (db.session.query(func.sum(Reservation.cost))
                     .filter(Reservation.status == 'completed', *conds).scalar() or 0)
    total_res_count  = Reservation.query.filter(*conds).count()
    completed_count  = Reservation.query.filter(Reservation.status == 'completed', *conds).count()
    avg_cost         = round(total_revenue / completed_count, 2) if completed_count else 0
    unique_users_cnt = (db.session.query(func.count(func.distinct(Reservation.user_id)))
                        .filter(*conds).scalar() or 0)

    top_users = (db.session.query(User, func.sum(Reservation.cost).label('spent'))
                 .join(Reservation, Reservation.user_id == User.id)
                 .filter(Reservation.status == 'completed', *conds)
                 .group_by(User.id)
                 .order_by(func.sum(Reservation.cost).desc())
                 .limit(5).all())
    for u, _ in top_users:
        u.booking_count = Reservation.query.filter(
            Reservation.user_id == u.id, *conds).count()

    day_col = func.date(Reservation.check_in).label('day')
    daily = (db.session.query(
                 day_col,
                 func.count().label('cnt'),
                 func.sum(Reservation.cost).label('rev'))
             .filter(Reservation.status == 'completed', *conds)
             .group_by(day_col)
             .order_by(day_col.desc())
             .limit(14).all())

    lot_breakdown = (db.session.query(
                         ParkingLot,
                         func.count(Reservation.id).label('cnt'),
                         func.sum(Reservation.cost).label('rev'))
                     .join(Reservation, Reservation.lot_id == ParkingLot.id)
                     .filter(Reservation.status == 'completed', *conds)
                     .group_by(ParkingLot.id)
                     .order_by(func.sum(Reservation.cost).desc())
                     .all())

    detail_res = (Reservation.query.filter(*conds)
                  .order_by(Reservation.check_in.desc()).all())

    all_users = User.query.filter_by(is_admin=False).order_by(User.first_name).all()
    all_lots  = ParkingLot.query.order_by(ParkingLot.name).all()

    return render_template('admin-reports.html',
        total_revenue=total_revenue, total_res_count=total_res_count,
        completed_count=completed_count, avg_cost=avg_cost,
        unique_users_cnt=unique_users_cnt,
        top_users=top_users, daily=daily,
        lot_breakdown=lot_breakdown, detail_res=detail_res,
        all_users=all_users, all_lots=all_lots,
        date_from=date_from_str, date_to=date_to_str,
        sel_user_ids=sel_user_ids, sel_lot_ids=sel_lot_ids,
        is_filtered=is_filtered, now=datetime.now())

@app.route('/admin/release/<int:res_id>', methods=['POST'])
@login_required
@admin_required
def admin_release(res_id):
    res = db.get_or_404(Reservation, res_id)
    _release_reservation(res)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reports/csv')
@login_required
@admin_required
def admin_reports_csv():
    date_from_str = request.args.get('date_from', '').strip()
    date_to_str   = request.args.get('date_to', '').strip()
    sel_user_ids  = request.args.getlist('user_ids', type=int)
    sel_lot_ids   = request.args.getlist('lot_ids', type=int)

    conds   = _report_filters(date_from_str, date_to_str, sel_user_ids, sel_lot_ids)
    all_res = (Reservation.query.filter(*conds)
               .order_by(Reservation.check_in.desc()).all())

    parts = ['parkvault-report']
    if date_from_str: parts.append(date_from_str)
    if date_to_str:   parts.append('to-' + date_to_str)
    filename = '-'.join(parts) + '.csv'

    out = io.StringIO()
    out.write('\ufeff')          # UTF-8 BOM — makes Excel open correctly
    w = csv.writer(out)
    w.writerow(['#', 'User', 'Email', 'Lot', 'Spot',
                'Check In', 'Check Out', 'Duration', 'Cost (INR)', 'Status'])
    for sno, r in enumerate(all_res, start=1):
        if r.check_out and r.check_in:
            secs     = int((r.check_out - r.check_in).total_seconds())
            duration = f"{secs//3600}h {(secs%3600)//60}m"
        else:
            duration = 'Ongoing' if r.status == 'active' else '-'
        w.writerow([
            sno, r.user.name, r.user.email, r.lot.name, r.spot_number,
            r.check_in.strftime('%d %b %Y  %I:%M %p'),
            r.check_out.strftime('%d %b %Y  %I:%M %p') if r.check_out else '-',
            duration,
            f'{r.cost:.2f}' if r.cost else '0.00',
            r.status.capitalize()
        ])
    return Response(
        out.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

# ── Database & User CRUD routes ───────────────────────────────────────────────

@app.route('/admin/database')
@login_required
@admin_required
def admin_database():
    users = User.query.order_by(User.joined.desc()).all()
    for u in users:
        u.booking_count = Reservation.query.filter_by(user_id=u.id).count()
        u.total_spent   = (db.session.query(func.sum(Reservation.cost))
                           .filter(Reservation.user_id == u.id,
                                   Reservation.status == 'completed')
                           .scalar() or 0)
    total_users        = len(users)
    admin_count        = sum(1 for u in users if u.is_admin)
    regular_count      = total_users - admin_count
    total_reservations = Reservation.query.count()
    active_res_count   = Reservation.query.filter_by(status='active').count()
    completed_res      = Reservation.query.filter_by(status='completed').count()
    total_lots         = ParkingLot.query.count()
    total_spots        = Spot.query.count()
    flash_messages     = []
    return render_template('admin-database.html',
        users=users, total_users=total_users,
        admin_count=admin_count, regular_count=regular_count,
        total_reservations=total_reservations,
        active_res_count=active_res_count,
        completed_res=completed_res,
        total_lots=total_lots, total_spots=total_spots)

@app.route('/admin/database/query', methods=['POST'])
@login_required
@admin_required
def admin_db_query():
    sql = (request.json or {}).get('sql', '').strip()
    if not sql:
        return jsonify({'error': 'No query provided.'}), 400
    try:
        start   = time.perf_counter()
        result  = db.session.execute(text(sql))
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        if result.returns_rows:
            columns = list(result.keys())
            rows    = [[str(v) if v is not None else 'NULL' for v in row]
                       for row in result.fetchall()]
            return jsonify({
                'type': 'select', 'columns': columns,
                'rows': rows, 'count': len(rows), 'ms': elapsed
            })
        else:
            db.session.commit()
            return jsonify({
                'type': 'dml', 'rowcount': result.rowcount, 'ms': elapsed
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/admin/database/schema')
@login_required
@admin_required
def admin_db_schema():
    """Return table names, column names+types, and row counts as JSON."""
    inspector = inspect(db.engine)
    tables    = {}
    for tbl in inspector.get_table_names():
        cols = [{'name': c['name'], 'type': str(c['type'])}
                for c in inspector.get_columns(tbl)]
        try:
            count = db.session.execute(text(f'SELECT COUNT(*) FROM "{tbl}"')).scalar()
        except Exception:
            count = '?'
        tables[tbl] = {'columns': cols, 'count': count}
    return jsonify(tables)

@app.route('/admin/database/users/add', methods=['POST'])
@login_required
@admin_required
def admin_db_add_user():
    email = request.form.get('email', '').strip().lower()
    if User.query.filter_by(email=email).first():
        flash('A user with that email already exists.', 'error')
        return redirect(url_for('admin_users'))
    pw = request.form.get('password', '').strip()
    if not pw:
        flash('Password is required when creating a user.', 'error')
        return redirect(url_for('admin_users'))
    user = User(
        first_name    = request.form.get('fname', '').strip(),
        last_name     = request.form.get('lname', '').strip(),
        email         = email,
        phone         = request.form.get('phone', '').strip(),
        vehicle       = request.form.get('vehicle', '').strip(),
        password_hash = bcrypt.generate_password_hash(pw).decode(),
        is_admin      = request.form.get('role') == 'admin'
    )
    db.session.add(user)
    db.session.commit()
    flash(f'User {user.name} created successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/database/users/edit/<int:uid>', methods=['POST'])
@login_required
@admin_required
def admin_db_edit_user(uid):
    u     = db.get_or_404(User, uid)
    email = request.form.get('email', u.email).strip().lower()
    # Check email conflict (ignore own current email)
    conflict = User.query.filter(User.email == email, User.id != uid).first()
    if conflict:
        flash('That email is already used by another account.', 'error')
        return redirect(url_for('admin_users'))
    u.first_name = request.form.get('fname', u.first_name).strip()
    u.last_name  = request.form.get('lname', u.last_name).strip()
    u.email      = email
    u.phone      = request.form.get('phone', u.phone or '').strip()
    u.vehicle    = request.form.get('vehicle', u.vehicle or '').strip()
    # Prevent removing own admin role
    if uid != current_user.id:
        u.is_admin = request.form.get('role') == 'admin'
    pw = request.form.get('password', '').strip()
    if pw:
        u.password_hash = bcrypt.generate_password_hash(pw).decode()
    db.session.commit()
    flash(f'User {u.name} updated successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/database/users/delete/<int:uid>', methods=['POST'])
@login_required
@admin_required
def admin_db_delete_user(uid):
    if uid == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_users'))
    u = db.get_or_404(User, uid)
    name = u.name
    # Release any active reservations first
    for res in Reservation.query.filter_by(user_id=uid, status='active').all():
        _release_reservation(res)
    Reservation.query.filter_by(user_id=uid).delete()
    db.session.delete(u)
    db.session.commit()
    flash(f'User {name} and all their data have been deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/database/users/role/<int:uid>', methods=['POST'])
@login_required
@admin_required
def admin_db_toggle_role(uid):
    if uid == current_user.id:
        flash('You cannot change your own role.', 'error')
        return redirect(url_for('admin_users'))
    u = db.get_or_404(User, uid)
    u.is_admin = not u.is_admin
    db.session.commit()
    role_label = 'Admin' if u.is_admin else 'User'
    flash(f'{u.name} is now a {role_label}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/database/users/export')
@login_required
@admin_required
def admin_db_export_users():
    users = User.query.order_by(User.joined.desc()).all()
    out = io.StringIO()
    out.write('\ufeff')          # UTF-8 BOM — makes Excel open correctly
    w   = csv.writer(out)
    w.writerow(['ID', 'First Name', 'Last Name', 'Email', 'Phone',
                'Vehicle', 'Role', 'Status', 'Joined', 'Reservations', 'Total Spent (INR)'])
    for sno, u in enumerate(users, start=1):
        bookings = Reservation.query.filter_by(user_id=u.id).count()
        spent    = (db.session.query(func.sum(Reservation.cost))
                    .filter(Reservation.user_id == u.id,
                            Reservation.status == 'completed')
                    .scalar() or 0)
        w.writerow([
            sno,
            u.first_name,
            u.last_name,
            u.email,
            u.phone or '-',
            u.vehicle or '-',
            'Admin' if u.is_admin else 'User',
            u.status.capitalize(),
            u.joined.strftime('%d %b %Y') if u.joined else '-',
            bookings,
            f'{spent:.2f}'
        ])
    return Response(
        out.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=parkvault-users-export.csv'}
    )

# ── Email trigger routes ──────────────────────────────────────────────────────

@app.route('/admin/send-monthly-report', methods=['POST'])
@login_required
@admin_required
def admin_send_monthly_report():
    sent = send_monthly_report_email()
    flash(f'Monthly report sent to {sent} admin(s).', 'success')
    return redirect(url_for('admin_reports'))


# ── Background scheduler ──────────────────────────────────────────────────────
# Runs only in the main serving process (not the Werkzeug reloader watcher).

def _ctx(fn):
    """Wrap a job function so it runs inside the Flask app context."""
    def wrapper():
        with app.app_context():
            fn()
    return wrapper

_run_main = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
if _run_main or not app.debug:
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(_ctx(send_long_stay_alerts),    'interval', hours=1,
                       id='long_stay_alerts',    replace_existing=True)
    _scheduler.add_job(_ctx(send_daily_admin_summary), 'cron', hour=8, minute=0,
                       id='daily_admin_summary', replace_existing=True)
    _scheduler.start()
    atexit.register(lambda: _scheduler.shutdown(wait=False))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_db()
    app.run(debug=True, port=5001)
