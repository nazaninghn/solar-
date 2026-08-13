from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.rate_limit import enforce_login_rate_limit
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.modules.auth.service import (
    authenticate_user,
    create_tokens,
    logout as logout_service,
    refresh_access_token,
    register_user,
    request_password_reset,
    resend_verification_email,
    reset_password,
    verify_email,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        user = register_user(
            db=db,
            email=data.email,
            password=data.password,
            full_name=data.full_name,
            organization_name=data.organization_name,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "organization_id": user.organization_id,
        "role": user.role,
    }


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # 24.35: rate-limited before touching the DB, so a credential-stuffing
    # burst can't be used to hammer authenticate_user's password hashing.
    enforce_login_rate_limit(request, data.email)

    user = authenticate_user(
        db=db,
        email=data.email,
        password=data.password,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return create_tokens(db, user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):
    try:
        return refresh_access_token(db, data.refresh_token)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    data: LogoutRequest,
    db: Session = Depends(get_db),
):
    logout_service(db, data.refresh_token)


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    request_password_reset(db, data.email)

    # Deliberately generic — see request_password_reset's docstring on
    # why this doesn't confirm whether the email is registered.
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
)
def reset_password_endpoint(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    try:
        reset_password(db, data.token, data.new_password)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    return {"message": "Password has been reset successfully."}


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
)
def verify_email_endpoint(
    data: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    try:
        verify_email(db, data.token)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    return {"message": "Email verified successfully."}


@router.post(
    "/resend-verification",
    status_code=status.HTTP_200_OK,
)
def resend_verification_endpoint(
    data: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    resend_verification_email(db, data.email)

    return {"message": "If that email is registered and unverified, a new link has been sent."}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "organization": {
            "id": current_user.organization.id,
            "name": current_user.organization.name,
        },
    }
