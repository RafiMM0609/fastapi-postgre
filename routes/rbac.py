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

from schemas.rbac import (
    RoleManagementSchema,
    UpdatePermissionRequest,
    UpdatePermissionResponse,
    UpdateMultiplePermissionRequest,
    UpdateMultiplePermissionResponse,
)

import repository.rbac as rbacRepo

router = APIRouter(tags=["Role Management"])
@router.get(
    "/role-management",
    response_model=RoleManagementSchema,  # Pastikan model responsnya benar
    responses={
        200: {"model": RoleManagementSchema},
        400: {"model": BadRequestResponse},
        401: {"model": UnauthorizedResponse},
        404: {"model": NotFoundResponse},
        500: {"model": InternalServerErrorResponse},
    },
)
async def role_management(
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await rbacRepo.get_role_management(db)
        return common_response(
            Ok(data=data)
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in role_management endpoint: {str(e)}\n{error_details}")
        return common_response(InternalServerError())


@router.put(
    "/update-multiple-permission",
    response_model=UpdateMultiplePermissionResponse,
    responses={
        200: {"model": UpdateMultiplePermissionResponse},
        400: {"model": BadRequestResponse},
        401: {"model": UnauthorizedResponse},
        404: {"model": NotFoundResponse},
        500: {"model": InternalServerErrorResponse},
    },
)
async def update_multiple_permission(
    request: UpdateMultiplePermissionRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        updated_permissions = []
        for permission in request.permissions:
            data = await rbacRepo.update_permission(
                db=db,
                role_id=permission.role_id,
                permission_id=permission.permission_id,
                isact=permission.isact,
            )
            updated_permissions.append(data)
            
        return common_response(
            Ok(data={"updated_permissions": updated_permissions}, message="Permissions updated successfully")
        )
    except ValueError as e:
        return common_response(BadRequest(message=str(e)))
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in update_multiple_permission endpoint: {str(e)}\n{error_details}")
        return common_response(InternalServerError())