from flask import Flask
import redis
from flask_sqlalchemy import SQLAlchemy
import os
import time
from sqlalchemy.exc import OperationalError  # Import for catching DB errors
from urllib.parse import quote_plus

app = Flask(__name__)

# Environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Active@53")
password_encoded = quote_plus(MYSQL_PASSWORD)
MYSQL_HOST = os.getenv("MYSQL_HOST", "db")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "testdb")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")

# Redis setup
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# SQLAlchemy config
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{MYSQL_USER}:{password_encoded}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Database model
class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(100))


# Route
@app.route("/")
def home():
    r.incr("hits")
    hits = r.get("hits")

    if Visitor.query.count() == 0:
        db.session.add(Visitor(message="Hello from SQLAlchemy + MySQL"))
        db.session.commit()

    visitor = Visitor.query.first()
    return {"message": visitor.message, "redis_hits": hits}


# Retry logic for DB initialization
with app.app_context():
    max_retries = 10
    retry_delay = 3  # seconds

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} to connect to database...")
            db.create_all()
            print("Database connected and tables created.")
            break
        except OperationalError as e:
            print(f"Database connection failed: {e}")
            time.sleep(retry_delay)
    else:
        print("Failed to connect to database after several attempts. Exiting.")
        exit(1)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)