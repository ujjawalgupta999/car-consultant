import uuid
import hashlib
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from ..repositories.session import session_repo

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None

class UserLoginRequest(BaseModel):
    email: str
    password: str

# Simple in-memory user store
_USERS_DB: Dict[str, Dict[str, Any]] = {
    "demo@auramotors.com": {
        "id": "usr_demo_01",
        "name": "Alex Vance",
        "email": "demo@auramotors.com",
        "password_hash": hashlib.sha256("Password123!".encode()).hexdigest(),
        "phone": "+91 98765 43210",
        "saved_vehicles": ["CAR-001", "CAR-021"],
        "created_at": "2026-11-01T10:00:00Z"
    }
}

_TOKENS_DB: Dict[str, str] = {
    "token_demo_alex_vance": "demo@auramotors.com"
}

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/signup", status_code=201)
def signup(req: UserRegisterRequest):
    email = req.email.lower().strip()
    if email in _USERS_DB:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    
    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    pw_hash = _hash_pw(req.password)
    user = {
        "id": user_id,
        "name": req.name.strip(),
        "email": email,
        "password_hash": pw_hash,
        "phone": req.phone or "+91 98765 00000",
        "saved_vehicles": [],
        "created_at": "2026-11-05T12:00:00Z"
    }
    _USERS_DB[email] = user
    token = f"token_{uuid.uuid4().hex[:16]}"
    _TOKENS_DB[token] = email

    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {
        "user": safe_user,
        "token": token,
        "message": "Account created successfully."
    }

@router.post("/login")
def login(req: UserLoginRequest):
    email = req.email.lower().strip()
    user = _USERS_DB.get(email)
    if not user or user["password_hash"] != _hash_pw(req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = f"token_{uuid.uuid4().hex[:16]}"
    _TOKENS_DB[token] = email

    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {
        "user": safe_user,
        "token": token,
        "message": "Logged in successfully."
    }

@router.get("/me")
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        # Return guest profile
        return {
            "authenticated": False,
            "user": None
        }

    token = authorization.replace("Bearer ", "").strip()
    email = _TOKENS_DB.get(token)
    if not email or email not in _USERS_DB:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    user = _USERS_DB[email]
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {
        "authenticated": True,
        "user": safe_user
    }

@router.post("/saved-vehicles/toggle")
def toggle_saved_vehicle(payload: Dict[str, str], authorization: Optional[str] = Header(None)):
    vehicle_id = payload.get("vehicle_id")
    if not vehicle_id:
        raise HTTPException(status_code=400, detail="vehicle_id is required")

    email = "demo@auramotors.com"
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        if token in _TOKENS_DB:
            email = _TOKENS_DB[token]

    user = _USERS_DB.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    saved = user["saved_vehicles"]
    if vehicle_id in saved:
        saved.remove(vehicle_id)
        is_saved = False
    else:
        saved.append(vehicle_id)
        is_saved = True

    return {
        "vehicle_id": vehicle_id,
        "is_saved": is_saved,
        "total_saved": len(saved),
        "saved_vehicles": saved
    }

