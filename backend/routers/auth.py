import hashlib
import os
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.database import get_supabase

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    user_id: str
    username: str


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=260_000,
    ).hex()


@router.post("/auth/register", response_model=AuthResponse)
async def register(body: RegisterRequest):
    if len(body.username) < 3:
        raise HTTPException(status_code=422, detail="Username must be at least 3 characters")
    if len(body.password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters")

    db = get_supabase()

    existing = db.table("users").select("id").eq("username", body.username).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Username already taken")

    salt = os.urandom(32).hex()
    password_hash = _hash_password(body.password, salt)

    row = {
        "id": str(uuid.uuid4()),
        "username": body.username,
        "password_hash": password_hash,
        "salt": salt,
    }
    if body.email:
        row["email"] = body.email

    result = db.table("users").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create user")

    created = result.data[0]
    return AuthResponse(user_id=created["id"], username=created["username"])


@router.post("/auth/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    db = get_supabase()

    result = db.table("users").select("id, username, password_hash, salt").eq("username", body.username).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user = result.data[0]
    expected = _hash_password(body.password, user["salt"])
    if expected != user["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return AuthResponse(user_id=user["id"], username=user["username"])
