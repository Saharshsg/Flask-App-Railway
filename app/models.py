from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import jwt
from datetime import datetime, timedelta, timezone, date
from flask import current_app
from sqlalchemy import UniqueConstraint, Text
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from typing import Optional


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    is_intern = db.Column(db.Boolean, default=False)
    
    schedule_entries = relationship('Schedule', back_populates='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': datetime.now(timezone.utc) + timedelta(seconds=expires_in)},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']
        except:
            return None
        return db.session.get(User, id)

    def __repr__(self):
        return f'<User {self.username}>'

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class WeekConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_start_date = db.Column(db.Date, unique=True, index=True)  # Monday of the week
    is_locked = db.Column(db.Boolean, default=True)  # New weeks are locked by default
    created_by = db.Column(db.Integer, sa.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WeekConfig {self.week_start_date}: {"Locked" if self.is_locked else "Unlocked"}>'


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, sa.ForeignKey('user.id'), index=True)
    date = db.Column(db.Date, index=True)
    status = db.Column(db.String(10))
    meal_preference = db.Column(db.String(10), nullable=True)  # Now supports "No Meal" option
    was_auto_assigned = db.Column(db.Boolean, default=False)
    reassignment_request = db.Column(db.Boolean, default=False)
    reassignment_reason = db.Column(db.String(300), nullable=True)
    is_available = db.Column(db.Boolean, default=False)

    user = relationship('User', back_populates='schedule_entries')

    __table_args__ = (sa.UniqueConstraint('user_id', 'date', name='_user_date_uc'),)

    def __repr__(self):
        return f'<Schedule {self.user.username} on {self.date}: {self.status}>' 