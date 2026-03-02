from website import db

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(200), nullable=False)
    user = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True  # nullable so that we can log visits without a user
    )
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Visit id={self.id} page='{self.page}' timestamp={self.timestamp}>"

class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    atype = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class Error(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    error_type = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(500), nullable=True)
    user_email = db.Column(db.String(80), nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Error id={self.id} type='{self.error_type}' timestamp={self.timestamp}>"
