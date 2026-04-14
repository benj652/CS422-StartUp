from website import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    # This stores the UUID for anonymous tracking until they "sign up" or identify
    uuid = db.Column(db.String(100), unique=True, nullable=False)
    # Log info from onboarding form
    class_year = db.Column(db.String(50))
    major = db.Column(db.String(100))
    career_goal = db.Column(db.String(100))
    career_stage = db.Column(db.String(100))
    priority = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationship to see user actions and visits easily
    visits = db.relationship("Visit", backref="visitor", lazy=True)
    actions = db.relationship("Action", backref="actor", lazy=True)


class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Visit id={self.id} page='{self.page}' timestamp={self.timestamp}>"


class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    atype = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Feedback id={self.id} created_at={self.created_at}>"


class Error(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    error_type = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(500), nullable=True)
    user_email = db.Column(db.String(80), nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return (
            f"<Error id={self.id} type='{self.error_type}' timestamp={self.timestamp}>"
        )
