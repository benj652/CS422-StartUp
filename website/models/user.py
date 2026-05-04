"""User model and authentication helpers.

Defines the User SQLAlchemy model used for authentication and role checks.
"""

from flask_login import UserMixin

from website import db

class User(db.Model, UserMixin):
    """Application user with authentication and role information."""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    profile_picture = db.Column(db.String(200))

    def __repr__(self):
        """Return a concise representation for debugging."""
        return f"<User {self.email}>"

    def to_dict(self):
        """Return a JSON-serializable representation of the user."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "profile_picture": self.profile_picture,
        }

    def save(self):
        """Save the user to the database"""
        db.session.add(self)
        db.session.commit()
