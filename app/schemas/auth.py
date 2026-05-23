from pydantic import BaseModel


class LoginInitResponse(BaseModel):
    authorize_url: str
    state: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
