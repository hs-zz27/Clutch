from pydantic import BaseModel, Field

class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    display_name: str | None = Field(default=None, max_length=255)

class LoginRequest(BaseModel):
    email: str
    password: str

class UserRead(BaseModel):
    id: int
    email: str
    display_name: str | None = None
    is_demo: bool

    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
