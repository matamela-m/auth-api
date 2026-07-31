import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from supabase_auth.errors import AuthApiError
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Auth Practice API")

security = HTTPBearer(auto_error=False)


@app.on_event("startup")
async def startup_event():
    print("Server running and connected to Supabase")


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Access token required")

    token = credentials.credentials

    try:
        response = supabase.auth.get_user(token)
        return response.user
    except AuthApiError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


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


@app.post("/auth/logout", status_code=204)
async def logout(user=Depends(get_current_user)):
    supabase.auth.sign_out()
    return


@app.get("/public/info", status_code=200)
async def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", status_code=200)
async def protected_profile(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }


@app.get("/protected/dashboard", status_code=200)
async def protected_dashboard(user=Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {user.email}"}