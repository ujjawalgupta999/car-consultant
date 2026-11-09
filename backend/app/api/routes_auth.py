import uuid
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from ..db.mongodb import mongodb_manager

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None

class UserLoginRequest(BaseModel):
    email: str
    password: str

# In-memory fallback cache
_USERS_CACHE: Dict[str, Dict[str, Any]] = {
    "demo@auramotors.com": {
        "id": "usr_demo_01",
        "name": "Alex Vance",
        "email": "demo@auramotors.com",
        "password_hash": hashlib.sha256("Password123!".encode()).hexdigest(),
        "phone": "+91 98765 43210",
        "saved_vehicles": ["CAR-001", "CAR-021"],
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z"
    }
}

_TOKENS_CACHE: Dict[str, str] = {
    "token_demo_alex_vance": "demo@auramotors.com"
}

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _get_users_collection():
    return mongodb_manager.get_collection("users")

def _get_tokens_collection():
    return mongodb_manager.get_collection("user_tokens")

def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    norm_email = email.lower().strip()
    coll = _get_users_collection()
    if coll is not None:
        try:
            doc = coll.find_one({"email": norm_email}, {"_id": 0})
            if doc:
                return doc
        except Exception:
            pass
    return _USERS_CACHE.get(norm_email)

def find_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    coll = _get_users_collection()
    if coll is not None:
        try:
            doc = coll.find_one({"id": user_id}, {"_id": 0})
            if doc:
                return doc
        except Exception:
            pass
    for u in _USERS_CACHE.values():
        if u.get("id") == user_id:
            return u
    return None

def save_user(user_doc: Dict[str, Any]):
    norm_email = user_doc["email"].lower().strip()
    _USERS_CACHE[norm_email] = user_doc
    coll = _get_users_collection()
    if coll is not None:
        try:
            coll.update_one({"email": norm_email}, {"$set": user_doc}, upsert=True)
        except Exception as e:
            pass

def record_token(token: str, email: str):
    _TOKENS_CACHE[token] = email.lower().strip()
    t_coll = _get_tokens_collection()
    if t_coll is not None:
        try:
            t_coll.update_one(
                {"token": token},
                {"$set": {"token": token, "email": email.lower().strip(), "created_at": datetime.utcnow().isoformat() + "Z"}},
                upsert=True
            )
        except Exception:
            pass

def resolve_email_from_token(token: str) -> Optional[str]:
    if token in _TOKENS_CACHE:
        return _TOKENS_CACHE[token]
    t_coll = _get_tokens_collection()
    if t_coll is not None:
        try:
            doc = t_coll.find_one({"token": token}, {"_id": 0})
            if doc and "email" in doc:
                _TOKENS_CACHE[token] = doc["email"]
                return doc["email"]
        except Exception:
            pass
    return None

def resolve_user_id(authorization: Optional[str] = None) -> str:
    """Derives user ID from session/token, defaulting to demo user in demo environment."""
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        email = resolve_email_from_token(token)
        if email:
            user = find_user_by_email(email)
            if user:
                return user["id"]
    return "usr_demo_01"

@router.post("/signup", status_code=201)
def signup(req: UserRegisterRequest):
    email = req.email.lower().strip()
    existing = find_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    pw_hash = _hash_pw(req.password)
    now_iso = datetime.utcnow().isoformat() + "Z"
    user = {
        "id": user_id,
        "name": req.name.strip(),
        "email": email,
        "phone": req.phone or "+91 98765 00000",
        "password_hash": pw_hash,
        "saved_vehicles": [],
        "created_at": now_iso,
        "updated_at": now_iso
    }
    save_user(user)

    token = f"token_{uuid.uuid4().hex[:16]}"
    record_token(token, email)

    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {
        "user": safe_user,
        "token": token,
        "message": "Account created successfully."
    }

@router.post("/login")
def login(req: UserLoginRequest):
    email = req.email.lower().strip()
    user = find_user_by_email(email)
    if not user or user.get("password_hash") != _hash_pw(req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = f"token_{uuid.uuid4().hex[:16]}"
    record_token(token, email)

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
    email = resolve_email_from_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    user = find_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {
        "authenticated": True,
        "user": safe_user
    }

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None

@router.put("/profile")
def update_profile(req: UpdateProfileRequest, authorization: Optional[str] = Header(None)):
    email = "demo@auramotors.com"
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        e = resolve_email_from_token(token)
        if e:
            email = e

    user = find_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.name:
        user["name"] = req.name.strip()
    if req.phone:
        user["phone"] = req.phone.strip()
    if req.city:
        user["city"] = req.city.strip()
    user["updated_at"] = datetime.utcnow().isoformat() + "Z"

    save_user(user)

    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {
        "user": safe_user,
        "message": "Profile updated successfully."
    }

@router.post("/saved-vehicles/toggle")
def toggle_saved_vehicle(payload: Dict[str, str], authorization: Optional[str] = Header(None)):
    vehicle_id = payload.get("vehicle_id")
    if not vehicle_id:
        raise HTTPException(status_code=400, detail="vehicle_id is required")

    email = "demo@auramotors.com"
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        e = resolve_email_from_token(token)
        if e:
            email = e

    user = find_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    saved: List[str] = list(user.get("saved_vehicles", []))
    if vehicle_id in saved:
        saved.remove(vehicle_id)
        is_saved = False
    else:
        saved.append(vehicle_id)
        is_saved = True

    user["saved_vehicles"] = saved
    user["updated_at"] = datetime.utcnow().isoformat() + "Z"
    save_user(user)

    return {
        "vehicle_id": vehicle_id,
        "is_saved": is_saved,
        "total_saved": len(saved),
        "saved_vehicles": saved
    }

@router.get("/saved")
@router.get("/saved-vehicles")
def get_saved_vehicles(authorization: Optional[str] = Header(None)):
    email = "demo@auramotors.com"
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        e = resolve_email_from_token(token)
        if e:
            email = e

    user = find_user_by_email(email)
    if not user:
        return {"total": 0, "saved_vehicles": []}

    saved_ids = user.get("saved_vehicles", [])
    return {
        "userId": user.get("id"),
        "total": len(saved_ids),
        "saved_vehicles": saved_ids
    }
