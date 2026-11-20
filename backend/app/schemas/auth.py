from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.auth import EMAIL_RE


class RegisterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=320)
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=2, max_length=80)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip()
        if not EMAIL_RE.match(v):
            raise ValueError("Format email tidak valid.")
        return v


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    display_name: str
    role: str

    @field_validator("id", mode="before")
    @classmethod
    def _id(cls, v) -> str:
        return str(v)


class AuthOut(BaseModel):
    user: UserOut
    csrf_token: str


class TokenIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=10, max_length=200)


class EmailIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=320)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip()
        if not EMAIL_RE.match(v):
            raise ValueError("Format email tidak valid.")
        return v


class ResetConfirmIn(TokenIn):
    new_password: str = Field(min_length=12, max_length=128)
