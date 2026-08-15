import sqlite3
from pathlib import Path
from typing import Optional

from pwdlib import PasswordHash


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "users.db"

password_hash = PasswordHash.recommended()


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


def create_user(
    email: str,
    full_name: str,
    password: str,
):
    email = email.strip().lower()
    full_name = full_name.strip()

    if not email:
        raise ValueError("Email is required.")

    if not full_name:
        raise ValueError("Full name is required.")

    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    hashed_password = password_hash.hash(
        password
    )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (
                email,
                full_name,
                password_hash
            )
            VALUES (?, ?, ?)
            """,
            (
                email,
                full_name,
                hashed_password,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError:
        raise ValueError(
            "An account with this email already exists."
        )

    finally:
        connection.close()


def get_user_by_email(
    email: str,
) -> Optional[dict]:

    email = email.strip().lower()

    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            id,
            email,
            full_name,
            password_hash,
            created_at
        FROM users
        WHERE email = ?
        """,
        (email,),
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def verify_password(
    password: str,
    stored_hash: str,
) -> bool:

    return password_hash.verify(
        password,
        stored_hash,
    )


init_db()