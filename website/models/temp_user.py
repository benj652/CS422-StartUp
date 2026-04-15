from flask_login import UserMixin


class TempUser(UserMixin):
    def __init__(self, user_id, email=None, name=None):
        self.id = user_id
        self.email = email
        self.name = name
