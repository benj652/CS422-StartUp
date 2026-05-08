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

    # profile = {
    #     "major": major,
    #     "year": year_key,
    #     "career_goal": data.get("career_goal", ""),
    #     "career_stage": data.get("career_stage", ""),
    #     "priority": data.get("priority", ""),
    # }

    major = db.Column(db.String(50))
    year = db.Column(db.String(20))
    career_goal = db.Column(db.String(50))
    career_stage = db.Column(db.String(50))
    priority = db.Column(db.String(50))
    wishlist_items = db.relationship(
        "WishlistItem",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        """Return a concise representation for debugging."""
        return f"<User {self.email} Major {self.major} Year {self.year} career goal {self.career_goal} career stage: {self.career_stage} priority {self.priority}>"

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


class WishlistItem(db.Model):
    """Wishlist item saved from roadmap interactions for an authenticated user."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    roadmap_item_id = db.Column(db.String(255), nullable=False)
    label = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    section = db.Column(db.String(100), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    href = db.Column(db.String(500), nullable=True)
    priority = db.Column(db.String(20), nullable=False, default="low")
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "roadmap_item_id", name="uq_wishlist_user_roadmap_item"
        ),
    )

    def to_dict(self):
        """Return a JSON-serializable representation of the wishlist item."""
        return {
            "id": self.id,
            "roadmap_item_id": self.roadmap_item_id,
            "label": self.label or self.title,
            "title": self.title,
            "section": self.section,
            "summary": self.summary,
            "href": self.href,
            "priority": self.priority,
        }
