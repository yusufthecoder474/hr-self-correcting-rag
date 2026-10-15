import sqlite3
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

import jwt

load_dotenv()

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from auth import (
    create_user,
    get_user_by_email,
    verify_password,
)


router = APIRouter()

security = HTTPBearer(auto_error=False)


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if len(JWT_SECRET_KEY) < 32 or JWT_SECRET_KEY == "development-only-change-this-secret":
    raise RuntimeError("Set a unique JWT_SECRET_KEY of at least 32 characters outside source control.")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


def create_access_token(user_id: int):
    expires_at = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
):
    if credentials is None:
        raise HTTPException(401, "Authentication required.")
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired.",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token.",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token.",
        )

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token.",
        )

    user = None

    # auth.py currently exposes lookup by email,
    # so we retrieve the user directly from the database.
    import sqlite3

    from auth import get_connection

    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            id,
            email,
            full_name,
            created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()

    connection.close()

    if row is not None:
        user = dict(row)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found.",
        )

    return user


@router.post(
    "/register",
    response_model=UserResponse,
)
def register(request: RegisterRequest):

    if os.getenv("ALLOW_REGISTRATION", "false").lower() != "true":
        raise HTTPException(403, "Registration is disabled; contact the administrator.")

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters.",
        )

    try:
        user_id = create_user(
            email=request.email,
            full_name=request.full_name,
            password=request.password,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return UserResponse(
        id=int(user_id),
        full_name=request.full_name.strip(),
        email=request.email.strip().lower(),
    )


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(request: LoginRequest):

    user = get_user_by_email(
        request.email
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    password_ok = verify_password(
        request.password,
        user["password_hash"],
    )

    if not password_ok:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        int(user["id"])
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=int(user["id"]),
            full_name=user["full_name"],
            email=user["email"],
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    user=Depends(get_current_user)
):

    return UserResponse(
        id=int(user["id"]),
        full_name=user["full_name"],
        email=user["email"],
    )