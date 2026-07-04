from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user_id: int
    email: EmailStr
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
