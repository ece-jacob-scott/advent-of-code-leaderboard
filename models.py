from app import db


class User(db.Model):
    __tablename__ = "users"
    id: int = db.Column(db.Integer, primary_key=True)
    user_name: str = db.Column(db.String(120), unique=True)
    leaderboard: str = db.Column(db.Text())
    github_access_token: str = db.Column(db.String(250))
    email: str = db.Column(db.String(500))

    def __init__(self, user_name=None, github_access_token=None, email=None):
        self.user_name = user_name
        self.leaderboard = ""
        self.github_access_token = github_access_token
        self.email = email

    def __repr__(self):
        return f'<Entry {self.user_name!r}>'
