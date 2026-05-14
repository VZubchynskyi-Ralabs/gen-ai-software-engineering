import os
import sqlite3
from flask import Flask

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "database.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'other',
    priority TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    resolved_at TEXT,
    assigned_to TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL DEFAULT 'api',
    browser TEXT,
    device_type TEXT,
    classification_confidence REAL,
    classification_reasoning TEXT,
    classification_keywords TEXT
);
"""


def get_db(db_path=None):
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db(db_path=None):
    conn = get_db(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def create_app(db_path=None, testing=False):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or DB_PATH
    app.config["TESTING"] = testing

    init_db(app.config["DB_PATH"])

    from src.routes.tickets import tickets_bp
    from src.routes.classify import classify_bp

    app.register_blueprint(tickets_bp)
    app.register_blueprint(classify_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)

