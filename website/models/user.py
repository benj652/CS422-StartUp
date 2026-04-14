from flask_login import UserMixin
from website import db

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    class_year = db.Column(db.String(50))
    major = db.Column(db.String(100))
    career_goal = db.Column(db.String(100))
    career_stage = db.Column(db.String(100))
    priority = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    visits = db.relationship('Visit', backref='visitor', lazy=True)
    actions = db.relationship('Action', backref='actor', lazy=True)
