from app import db

class User(db.Model):
    __tablename__ = "users"
    id: int = db.Column(db.Integer, primary_key=True)
    user_name: str = db.Column(db.String(120), unique=True)
    leaderboard: str = db.Column(db.Text())

    def __init__(self, user_name=None):
        self.user_name = user_name
        self.leaderboard = ""

    def __repr__(self):
        return f'<Entry {self.user_name!r}>'
