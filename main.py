import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from supabase_auth.errors import AuthApiError
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Auth Practice API")


@app.on_event("startup")
async def startup_event():
    print("Server running and connected to Supabase")


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


@app.post("/auth/signup", status_code=201)
async def signup(payload: AuthRequest):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password
        })
        return {"user": response.user}
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login", status_code=200)
async def login(payload: AuthRequest):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password
        })
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }
    except AuthApiError:
        raise HTTPException(status_code=401, detail="Invalid login credentials")


@app.get("/public/info", status_code=200)
async def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", status_code=200)
async def protected_profile(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")

    parts = auth_header.split(" ")
    token = parts[1] if len(parts) > 1 and parts[1] else None

    if not token:
        raise HTTPException(status_code=401, detail="Access token required")

    try:
        response = supabase.auth.get_user(token)
        user = response.user
        return {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at
        }
    except AuthApiError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")