"""Auth request and response schemas."""

from pydantic import BaseModel, EmailStr, Field


class SendVerificationCodeRequest(BaseModel):
    """Request schema for sending verification code."""

    name: str = Field(..., min_length=1, max_length=100)
    surname: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    """Request schema for verifying code."""

    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class VerificationResponse(BaseModel):
    """Response schema for verification operations."""

    message: str
    email: str
    verified: bool = False


class CheckEmailResponse(BaseModel):
    """Response schema for email verification check."""

    email: str
    is_verified: bool
