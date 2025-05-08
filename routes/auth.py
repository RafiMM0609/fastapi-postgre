
import traceback
from core.file import generate_link_download
from core.mail import send_reset_password_email
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
from core.security import get_user_from_jwt_token, generate_jwt_token_from_user, get_user_permissions
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
    ForgotPasswordChangePasswordRequest,
    ForgotPasswordChangePasswordResponse,
    ForgotPasswordSendEmailRequest,
    LoginSuccessResponse,
    LoginSuccess,
    LoginRequest,
    MeSuccessResponse,
    MenuResponse,
    PermissionsResponse,
    EditUserRequest,
    SignUpRequest,
    ForgotPasswordSendEmailResponse,
    RoleOptionsResponse,
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
        is_valid = await authRepo.check_user_password(db, request.email, request.password)
        if not is_valid:
            return common_response(BadRequest(message="Invalid Credentials"))

        user = is_valid
        token = await generate_jwt_token_from_user(user=user)
        await authRepo.create_user_session(db=db, user_id=user.id, token=token)
        data_response = LoginSuccess(
            user_id=str(user.id),
            email=user.email,
            token=token,
        )
        return common_response(
            Ok(
                data=data_response.model_dump(),
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
        is_valid =await authRepo.check_user_password(
            db, form_data.username, form_data.password
        )
        if not is_valid:
            return common_response(BadRequest(message="Invalid Credentials"))
        user = is_valid
        token = await generate_jwt_token_from_user(user=user)
        await authRepo.create_user_session(db=db, user_id=user.id, token=token)
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
    page_size: int = 10,
    token: str = Depends(oauth2_scheme),
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
                return common_response(BadRequest(message=str(e)))


@router.get(
    "/detail-user/{user_id}",
    responses={
        "200": {"model": MeSuccessResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def detail_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    try:
        user = await authRepo.get_user_by_id(db=db, user_id=user_id)
        if not user:
            return common_response(NotFound(message="User tidak ditemukan"))
            
        return common_response(
            Ok(
                data={
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "isact": user.isact,
                    "phone": user.phone,
                    "image": generate_link_download(user.photo),
                    "role": {
                        "id": user.roles[0].id if user.roles else None,
                        "name": user.roles[0].name if user.roles else None,
                    },
                    "address": user.address,
                    "photo": generate_link_download(user.photo),
                }
            )
        )
    except Exception as e:
        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))

@router.put(
    "/edit-user/{user_id}",
    responses={
        "200": {"model": MeSuccessResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "404": {"model": NotFoundResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def edit_user(
    user_id: str,
    request: EditUserRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = await get_user_from_jwt_token(db, token)
        if not current_user:
            return common_response(Unauthorized())

        updated_user = await authRepo.edit_user(db=db, user_id=user_id, request=request)
        if not updated_user:
            return common_response(NotFound(message="User tidak ditemukan"))

        return common_response(
            Ok(
                data={
                    "id": str(updated_user.id),
                    "email": updated_user.email,
                    "name": updated_user.name,
                    "isact": updated_user.isact,
                    "phone": updated_user.phone,
                    "image": generate_link_download(updated_user.photo),
                    "role": {
                        "id": updated_user.roles[0].id if updated_user.roles else None,
                        "name": updated_user.roles[0].name if updated_user.roles else None,
                    },
                    "address": updated_user.address,
                    "photo": generate_link_download(updated_user.photo),
                },
                message="Berhasil mengupdate data user"
            )
        )
    except Exception as e:
        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))

@router.post(
    "/forgot-password/send-email",
    responses={
        "200": {"model": ForgotPasswordSendEmailResponse},
        "400": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def request_forgot_password_send_email(
    request: ForgotPasswordSendEmailRequest,
    db: Session = Depends(get_db)
    # token: str = Depends(oauth2_scheme)
):
    try:
        user= await authRepo.get_user_by_email(db=db, email=request.email)
        if user == None:
            return common_response(BadRequest(message='user not found'))

        token = await authRepo.generate_token_forgot_password(db=db, user=user)
        await send_reset_password_email(
            email_to=user.email, 
            body={
                "email": user.email,
                "token": token,
            })
        return common_response(
            Ok(
                message="success kirim email ganti password, silahkan cek email anda"
            )
        )
    except Exception as e:
        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))

@router.post(
    "/forgot-password/change-password",
    responses={
        "200": {"model": ForgotPasswordChangePasswordResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def request_forgot_password_change_password(
    request: ForgotPasswordChangePasswordRequest,
    db: Session = Depends(get_db)
):
    try:
        user = await authRepo.change_user_password_by_token(
            db=db, token=request.token, new_password=request.password
        )
        if user == None:
            return common_response(BadRequest(message="User Not Found"))
        elif user == False:
            return common_response(Unauthorized(message="Invalid/Expired Token for Change Password"))

        return common_response(Ok(message="success menganti password anda"))
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.post(
    "/signup",
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
    
@router.get(
    "/me",
    responses={
        "200": {"model": MeSuccessResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def me(
        request: Request,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme)
        ):
    try:
        user = await get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        old_token = token
        print(user)
        refresh_token = await generate_jwt_token_from_user(user=user)
        return common_response(
            Ok(
                data={
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "isact": user.isact,
                    "phone": user.phone,
                    "refreshed_token": refresh_token,
                    "image": generate_link_download(user.photo),
                    "role": {
                        "id": user.roles[0].id if user.roles else None,
                        "name": user.roles[0].name if user.roles else None,
                    },
                    "address":user.address,
                    "photo": generate_link_download(user.photo),
                }
            )
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))
    
@router.get(
    "/permissions",
    responses={
        "200": {"model": PermissionsResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def permissions(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = await get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        user_permissions = get_user_permissions(db=db, user=user)
        return common_response(
            Ok(
                data={
                    "results": [
                        {
                            "id": x.id,
                            "permission": x.name,
                            "module": {
                                "id": x.module.id,
                                "nama": x.module.name,
                            }
                            if x.module != None
                            else None,
                        }
                        for x in user_permissions
                    ]
                },
                message="Success get permisson"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get(
    "/menu",
    responses={
        "200": {"model": MenuResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def menu(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        user = await get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())

        list_menu = await authRepo.generate_menu_tree_for_user(db=db, user=user)

        return common_response(Ok(data={"results": list_menu}))
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))

@router.post(
    "/logout",
    responses={
        "201": {"model": CudResponseSchema},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def logout_route(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        user = await get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        await authRepo.logout_user(db=db, user=user, token=token)
        return common_response(Ok(message="Successfully logged out."))
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))
    
@router.get(
    "/role-options",
    responses={
        "200": {"model": RoleOptionsResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def role_options(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    try:
        current_user = await get_user_from_jwt_token(db, token)
        if not current_user:
            return common_response(Unauthorized())

        role_options = await authRepo.get_role_options(db=db)
        
        return common_response(
            Ok(
                data={"results": role_options},
                message="Berhasil mendapatkan daftar role"
            )
        )
    except Exception as e:
        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))