from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    first_name    = db.Column(db.String(60))
    last_name     = db.Column(db.String(60))
    email         = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(256))
    phone         = db.Column(db.String(20), nullable=True)
    vehicle       = db.Column(db.String(50))
    status        = db.Column(db.String(20), default='active')  # active/parked/suspended
    is_admin      = db.Column(db.Boolean, default=False)
    joined        = db.Column(db.DateTime, default=db.func.now())
    reservations  = db.relationship('Reservation', backref='user', lazy=True)

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}" if self.first_name and self.last_name else "??"


class ParkingLot(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100))
    address       = db.Column(db.String(200))
    pin_code      = db.Column(db.String(10))
    lot_type      = db.Column(db.String(20))  # open/covered/multi-level
    total_spots   = db.Column(db.Integer)
    rate_per_hour = db.Column(db.Float)
    status        = db.Column(db.String(20), default='active')
    spots         = db.relationship('Spot', backref='lot', lazy=True)
    reservations  = db.relationship('Reservation', backref='lot', lazy=True)


class Spot(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    lot_id      = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_number = db.Column(db.String(10), nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    __table_args__ = (db.UniqueConstraint('lot_id', 'spot_number'),)


class Reservation(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'))
    lot_id      = db.Column(db.Integer, db.ForeignKey('parking_lot.id'))
    spot_number = db.Column(db.String(10))
    check_in    = db.Column(db.DateTime)
    check_out   = db.Column(db.DateTime, nullable=True)
    cost        = db.Column(db.Float, nullable=True)
    status      = db.Column(db.String(20), default='active')  # active/completed/cancelled
