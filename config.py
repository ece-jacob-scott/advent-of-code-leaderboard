from dotenv import load_dotenv
from os import path, environ

base_dir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(base_dir, '.env'))

TESTING = True
DEBUG = True
FLASK_ENV = environ.get("ENV")
SECRET_KEY = environ.get("SECRET_KEY")
SQLALCHEMY_DATABASE_URI = environ.get("DB_URL")
SESSION_PERMANENT = False
SESSION_TYPE = "filesystem"

