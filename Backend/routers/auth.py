"""
Authentication router — register, login, profile.
Uses Argon2id for password hashing (argon2-cffi).
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

import database as db
from auth_utils import create_access_token, require_current_user, get_current_user

router = APIRouter()

# Argon2id — memory 64 MB, time_cost 3, parallelism 2
_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


# ── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    if len(body.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")

    existing = await db.get_user_by_email_sqlite(body.email)
    if existing:
        raise HTTPException(409, "Email already registered")

    hashed = _ph.hash(body.password)
    user = await db.create_user_sqlite(body.name, body.email, hashed)

    token = create_access_token({"sub": user["uid"], "email": user["email"], "name": user["name"]})
    return {"access_token": token, "user": {"uid": user["uid"], "name": user["name"], "email": user["email"]}}


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    user_row = await db.get_user_by_email_sqlite(body.email)
    if not user_row:
        raise HTTPException(401, "Invalid email or password")

    try:
        _ph.verify(user_row["password_hash"], body.password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        raise HTTPException(401, "Invalid email or password")

    # Rehash if needed (Argon2 pepper upgrade)
    if _ph.check_needs_rehash(user_row["password_hash"]):
        new_hash = _ph.hash(body.password)
        # In a full implementation: update hash in DB
        pass

    token = create_access_token({"sub": user_row["uid"], "email": user_row["email"], "name": user_row["name"]})
    return {"access_token": token, "user": {"uid": user_row["uid"], "name": user_row["name"], "email": user_row["email"]}}


@router.get("/profile")
async def profile(current_user: dict = Depends(require_current_user)):
    user = await db.get_user_by_id_sqlite(current_user["sub"])
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.post("/logout")
async def logout():
    # JWT is stateless — client discards the token
    return {"message": "Logged out successfully"}
