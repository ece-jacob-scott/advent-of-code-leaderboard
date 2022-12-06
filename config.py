from dotenv import load_dotenv
from os import path, environ

base_dir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(base_dir, '.env'))

TESTING = True
DEBUG = True
FLASK_ENV = environ.get("ENV")
SECRET_KEY = environ.get("SECRET_KEY")
SQLALCHEMY_DATABASE_URI = environ.get("DB_URL")
SESSION_PERMANENT = True
SESSION_TYPE = "sqlalchemy"
# hopefully this fixes the issue where pg connection gets GC'd
# https://stackoverflow.com/questions/58866560/flask-sqlalchemy-pool-pre-ping-only-working-sometimes
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 60,
    'pool_pre_ping': True
}
