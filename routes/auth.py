import traceback
from fastapi import APIRouter, Depends, Request, BackgroundTasks, UploadFile, File, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from core.responses import (
    common_response,
    Ok,
    CudResponse,
    BadRequest,
    Unauthorized,
    NotFound,
    InternalServerError,
)
from models import get_db
from core.security import get_user_from_jwt_token, generate_jwt_token_from_user
from core.security import (
    get_user_from_jwt_token,
    oauth2_scheme,
)
from schemas.common import (
    BadRequestResponse,
    UnauthorizedResponse,
    NotFoundResponse,
    InternalServerErrorResponse,
    CudResponseSchema,
)
from schemas.auth import (
    ChangePasswordRequest,
    LoginSuccessResponse,
    LoginSuccess,
    LoginRequest,
    MeSuccessResponse,
    RegisSuccessResponse,
    SignUpRequest,
    SignupRequest,
    CadSuccessResponse,
    EditPassRequest,
    ListUserRequest,
    LoginTokenRequest,
)
import repository.auth  as authRepo
from urllib.parse import urlparse

router = APIRouter(tags=["Auth"])


@router.post(
    "/login",
    response_model=LoginSuccessResponse,
)
async def login_route(
    request: LoginRequest, 
    db: AsyncSession = Depends(get_db),
):
    try:        
        is_valid, status = await authRepo.check_user_password(db, request.email, request.password)
        if not is_valid:
            return common_response(BadRequest(message="Invalid Credentials"))

        user = is_valid
        token = await generate_jwt_token_from_user(user=user)
        if not user.first_login:
            await authRepo.create_user_session(db=db, user_id=user.id, token=token)
        data_response = LoginSuccess(
            user_id=str(user.id),
            email=user.email,
            token=token,
        )
        return common_response(
            Ok(
                data=LoginSuccess(**data_response).model_dump(),
                message="Success login",
            )
        )
    except Exception as e:
        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))
    

@router.post("/token")
async def generate_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        is_valid = authRepo.check_user_password(
            db, form_data.username, form_data.password
        )
        if not is_valid:
            return common_response(BadRequest(message="Invalid Credentials"))
        user = is_valid
        token = await generate_jwt_token_from_user(user=user)
        return {"access_token": token, "token_type": "Bearer"}
    except Exception as e:
        return common_response(BadRequest(message=str(e)))

@router.get(
    "/list-user",
    responses={
        "200": {"model": MeSuccessResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_user(
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 10
):
    try:
        data, num_data, num_page = await authRepo.list_user(db=db, page=page, page_size=page_size)
        print("disini")
        return common_response(
            Ok(
                meta={
                    "count": num_data,
                    "page_count": num_page,
                    "page_size": page_size,
                    "page": page,
                },
                data=data,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e))
)

@router.post(
    "/forgot-password/{email}",
    response_model=CudResponseSchema,
)
async def forgot_password_route(
        email: str,
        db: AsyncSession = Depends(get_db),
        ):
    try:
        await  authRepo.forgot_password(
            db=db,
            email=email
            )
        return common_response(
            CudResponse(
                message="Success Send Request Forgot Password",
            )
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))
    
    
@router.post(
    "/sign-up",
    response_model=CudResponseSchema,
)
async def sign_up_route(
        payload: SignUpRequest,
        db: AsyncSession = Depends(get_db),
        ):
    try:
        await  authRepo.sign_up(
            db=db,
            request=payload
            )
        return common_response(
            CudResponse(
                message="Success Sign Up",
            )
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))