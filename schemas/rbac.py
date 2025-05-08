from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class PermissionSchema(BaseModel):
    id: int
    module: Optional[str]
    access: bool


class RoleManagementSchema(BaseModel):
    role_id: int
    name: str
    description: Optional[str]
    group: Optional[str]
    access_feature: Optional[str] 
    permissions: List[PermissionSchema]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    isact: Optional[bool]


class UpdatePermissionRequest(BaseModel):
    role_id: int
    permission_id: int
    isact: bool


class UpdatePermissionResponse(BaseModel):
    role_id: int
    permission_id: int
    isact: bool
    message: str


class UpdateMultiplePermissionRequest(BaseModel):
    permissions: List[UpdatePermissionRequest]


class UpdateMultiplePermissionResponse(BaseModel):
    updated_permissions: List[UpdatePermissionResponse]
