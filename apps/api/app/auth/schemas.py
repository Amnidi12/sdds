import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.users.models import RoleName


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=200)
    role: RoleName = (
        RoleName.DONOR
    )  # NGO_ADMIN/SUPER_ADMIN accounts are provisioned by admins, not self-registration
    organization_id: uuid.UUID | None = None

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        """Enforce password complexity: at least one uppercase, one digit, one special character.
        Replaces the regex pattern which used lookaheads unsupported by Pydantic v2's Rust regex engine.
        """
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(not c.isalnum() for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(not c.isalnum() for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(not c.isalnum() for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class VerifyEmailRequest(BaseModel):
    token: str


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, max_length=30)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: RoleName
    organization_id: uuid.UUID | None
    is_email_verified: bool

    model_config = {"from_attributes": True}
