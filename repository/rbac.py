from typing import Optional, List
from sqlalchemy import select, and_, or_, update
from models.Role import Role
from models.Permission import Permission
from models.RolePermission import RolePermission
from models.Module import Module
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

async def get_role_management(
    db: AsyncSession,
    isact: Optional[bool] = True
) -> List[dict]:
    try:
        query = (
            select(Role)
            .filter(Role.isact == isact)
        )
        
        result = await db.execute(query)
        roles = result.scalars().all()
        
        role_list = []
        for role in roles:
            perm_query = (
                select(Permission, Module)
                .join(RolePermission, and_(
                    RolePermission.c.permission_id == Permission.id,
                    RolePermission.c.role_id == role.id,
                    RolePermission.c.isact == True
                ))
                .outerjoin(Module, Permission.module_id == Module.id)
                .filter(Permission.isact == True)
            )
            perm_result = await db.execute(perm_query)
            permissions_with_modules = perm_result.all()
            
            permissions_data = []
            for perm, module in permissions_with_modules:
                module_data = None
                if module:
                    module_data = module.name
                
                permissions_data.append({
                    "permission_id": perm.id,
                    "module": module_data,
                    "access": True
                })
            
            role_data = {
                "role_id": role.id,
                "name": role.name,
                "description": role.description,
                "role": role.group,
                "access_feature": role.access_feature,
                "permissions": permissions_data,
                "created_at": role.created_at,
                "updated_at": role.updated_at,
                "isact": role.isact
            }
            role_list.append(role_data)
            
        return role_list
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise ValueError(f"Error in get_role_management: {str(e)}\n{error_details}")
    
    
async def update_permission(
    db: AsyncSession,
    role_id: int,
    permission_id: int,
    isact: bool,
) -> dict:
    try:
        role = await db.execute(
            select(Role).filter(Role.id == role_id)
        )
        role = role.scalar_one_or_none()
        if not role:
            raise ValueError(f"Role dengan ID {role_id} tidak ditemukan")

        permission = await db.execute(
            select(Permission).filter(Permission.id == permission_id)
        )
        permission = permission.scalar_one_or_none()
        if not permission:
            raise ValueError(f"Permission dengan ID {permission_id} tidak ditemukan")

        existing_role_permission = await db.execute(
            select(RolePermission).filter(
                and_(
                    RolePermission.c.role_id == role_id,
                    RolePermission.c.permission_id == permission_id
                )
            )
        )
        existing_role_permission = existing_role_permission.scalar_one_or_none()

        if existing_role_permission:
            stmt = (
                update(RolePermission)
                .where(
                    and_(
                        RolePermission.c.role_id == role_id,
                        RolePermission.c.permission_id == permission_id
                    )
                )
                .values(isact=isact)
            )
            await db.execute(stmt)
        else:
            stmt = RolePermission.insert().values(
                role_id=role_id,
                permission_id=permission_id,
                isact=isact
            )
            await db.execute(stmt)

        await db.commit()

        return {
            "role_id": role_id,
            "permission_id": permission_id,
            "isact": isact,
        }

    except Exception as e:
        await db.rollback()
        raise ValueError(f"Error in update_permission: {str(e)}")
    
