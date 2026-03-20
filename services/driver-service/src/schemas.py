from pydantic import BaseModel


class RegisterDriverDto(BaseModel):
    username: str
    password: str


class LoginDriverDto(BaseModel):
    username: str
    password: str
