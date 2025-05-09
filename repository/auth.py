from typing import Optional, List, Dict, Any
from pytz import timezone
from sqlalchemy import or_, select, func, update, delete
from core.utils import generate_token, generate_token_custom
from models.ForgotPassword import ForgotPassword
from models.Menu import Menu
from models.Permission import Permission
from models.Role import Role
from models.UserRole import UserRole
from models.User import User
from models.UserToken import UserToken
from schemas.auth import (
    LoginSuccessResponse,
    LoginRequest,
    MenuDict,
    SignUpRequest,
    SignupRequest,
    EditPassRequest,
    EditUserRequest,
    OtpRequest,
)
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from core.security import (
    generate_hash_password,
    get_user_permissions,
    validated_user_password
)
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from schemas.auth import (
    LoginSuccess,
    Organization
)
from core.mail import send_reset_password_email
import secrets
import string
import traceback

from settings import TZ


async def change_user_password_by_token(
    db: AsyncSession, token: str, new_password: str
) -> Optional[User]:
    query = select(ForgotPassword).where(ForgotPassword.token == token)
    result = await db.execute(query)
    forgot_password = result.scalar()
    if forgot_password == None:
        return None

    if (forgot_password.created_date + timedelta(minutes=10)) < datetime.now():
        return False

    user_id = forgot_password.user_id
    user = await db.execute(select(User).filter(User.id == user_id))
    user = user.scalar()
    user.password = generate_hash_password(password=new_password)
    db.add(user)
    await db.execute(delete(ForgotPassword).where(ForgotPassword.user_id == user.id))
    await db.commit()
    return user

async def generate_token_forgot_password(db: AsyncSession, user: User) -> str:
    try:
        """
        generate token -> save user and token to database -> return generated token
        """
        token = generate_token_custom()
        forgot_password = ForgotPassword(user_id=user.id, token=token, created_date = datetime.now())
        db.add(forgot_password)
        await db.commit()
        return token
    except Exception as e:
        print("Error generate token forgot password", e)
        traceback.print_exc()
        raise ValueError("Failed to generate token forgot password")

async def logout_user(db:AsyncSession, user:User, token:str):
    try:
        result = await db.execute(
            select(UserToken).filter(
                UserToken.emp_id == user.id,
                UserToken.token == token,
                UserToken.isact == True
            )
        )
        exist_data = await result.scalar()
        # print("exist data", exist_data)
        if exist_data is not None:
            exist_data.isact = False
            db.add(exist_data)
            await db.commit()
        else:
            raise ValueError("User session not found")
        print("DISINI CO")
        return "oke"
    except Exception as e:
        print("Error logout_user",e)
        raise ValueError("Logout Failed")
    
    

#function to resend otp for forget  passworw
def expand_menu_tree_with_permissions(
    db: Session, root_menu: List[Menu], permissions: List[Permission]
) -> List[MenuDict]:
    if len(root_menu) == 0:
        return []
    else:
        return [
            {
                "id": y.id,
                "url": y.url,
                "name": y.name,
                "icon": y.icon,
                "is_has_child": y.is_has_child,
                "isact": y.isact,
                "is_show": y.is_show,
                "order": y.order_id if y.order_id != None else 0,
                "sub_menu": expand_menu_tree_with_permissions(
                    db=db, root_menu=y.child, permissions=permissions
                ),
            }
            for y in sorted(root_menu, key=lambda d: d.id)
            if y.isact == True
            and (
                y.permission_id in [x.id for x in permissions]
                # or y.permission_id == None
            )
        ]
def prune_menu_tree(trees: List[MenuDict]) -> List[MenuDict]:
    pruned_tree = []
    for tree in trees:
        if tree["is_has_child"] and len(tree["sub_menu"]) == 0:
            continue
        elif tree["is_has_child"] and len(tree["sub_menu"]) > 0:
            tree["sub_menu"] = prune_menu_tree(tree["sub_menu"])
        pruned_tree.append(tree)
    return pruned_tree
def sort_menu_tree_by_order(trees: List[MenuDict]) -> List[MenuDict]:
    return [
        {
            "id": y["id"],
            "title": y["name"],
            "path": y["url"],
            "icon": y["icon"],
            "is_show": y["is_show"],
            # "is_has_child": y["is_has_child"],
            # "is_active": y["is_active"],
            # "order": y["order"],
            "sub": sort_menu_tree_by_order(y["sub_menu"]) if len(y["sub_menu"]) > 0 else False,
        }
        for y in sorted(trees, key=lambda d: d["order"])
    ]
async def generate_menu_tree_for_user(db: Session, user: User) -> List[MenuDict]:
    try:
        permissions = get_user_permissions(db=db, user=user)
        query = select(Menu).options(
                selectinload(Menu.child)
            ).where(Menu.parent_id == None).order_by(Menu.id.asc())
        result = await db.execute(query)
        root_menu: List[Menu] = result.scalars().all()
        menu_tree = expand_menu_tree_with_permissions(
            db=db, root_menu=root_menu, permissions=permissions
        )
        menu_tree = prune_menu_tree(menu_tree)
        menu_tree = sort_menu_tree_by_order(menu_tree)
        print("menu tree", menu_tree)
        return menu_tree
    except Exception as e:
        traceback.print_exc()
        print("Error generate menu tree for user", e)
        raise ValueError("Failed to generate menu tree for user")

async def create_user_session(db: Session, user_id: str, token:str) -> str:
    try:
        exist_data = await db.execute(
            select(UserToken).filter(
                UserToken.emp_id == user_id,
                UserToken.token == token
            )
        )
        exist_data = exist_data.scalar()
        if exist_data is not None:
            exist_data.is_active = True
            db.add(exist_data)
            await db.commit()
        else:
            user_token = UserToken(emp_id=user_id, token=token)
            db.add(user_token)
            await db.commit()
        return 'succes'
    except Exception as e:
        print(f"Error creating user session: \n {e}")
        raise ValueError("Failed to create user session")
        
async def resend_forget_password_otp(db, email):
    try:
        # Check if the email exists in the database
        user_response = (
            db.table("user_tenant")
            .select("user_id, email")
            .eq("email", email)
            .execute()
        )

        if not user_response.data:
            raise ValueError("User with this email not found.")

        user_data = user_response.data[0] # Get the first user record
        user_id = user_data["user_id"]
        user_email = user_data["email"] # Correctly assign user_email
        random_token = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    
        expiry_time = datetime.now() + timedelta(minutes=10)
        insert_data = {
            "user_id": user_id,
            "token": random_token,
            "exp_datetime": expiry_time.isoformat(),
            "created_at": datetime.now().isoformat(),
        }
        token_insert_response = (
            db.table("user_login_token")
            .insert(insert_data)
            .execute()
        )

        await send_reset_password_email( 
            email_to=user_email, # Use the fetched user_email
            body={
                "email": user_email,
                "token": random_token,
            }
        )
        return True

    except ValueError as ve:
        raise ve
    except Exception as e:
        print(f"Error in resend_forget_password_otp for {email}: {e}")
        raise ValueError("Failed to process password reset request. Please try again later.")

async def forgot_password(db, email):
    try:
        # Query the user from the User model using SQLAlchemy
        query = select(User).filter(User.email == email)
        result = await db.execute(query)
        user_obj = await result.scalar()

        if not user_obj:
            raise ValueError("User with this email not found.")

        user_id = user_obj.id
        user_email = user_obj.email
        random_token = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        expiry_time = datetime.now() + timedelta(minutes=10)


        await send_reset_password_email( 
            email_to=user_email,
            body={
                "email": user_email,
                "token": random_token,
            }
        )
        return True

    except ValueError as ve:
        raise ve
    except Exception as e:
        print(f"Error in forgot_password for {email}: {e}")
        traceback.print_exc()
        raise ValueError("Failed to process password reset request. Please try again later.")

# set token to None and change password in user_tenant table
async def change_password(db, token, password):
    try:
        # 1. Find user_id based on the reset token (from user_login_token table)
        token_response = (
            db.table("user_login_token")
            .select("user_id, exp_datetime")
            .eq("token", token)
            .execute()
        )

        if not token_response.data:
            raise ValueError("Invalid or expired token.")

        token_data = token_response.data[0]
        user_id = token_data["user_id"]

        # 2. Check if token is valid and not expired
        if "exp_datetime" in token_data and datetime.fromisoformat(token_data["exp_datetime"]) < datetime.now():
             # 5. Invalidate or delete the used token from user_login_token (even if expired)
            db.table("user_login_token").delete().eq("token", token).execute()
            raise ValueError("Token has expired.")

        # 3. Hash the new password
        hashed_password = generate_hash_password(password)

        # 4. Update the password in the user_tenant table
        update_response = (
            db.table("user_tenant")
            .update({"password": hashed_password})
            .eq("user_id", user_id)
            .execute()
        )

        if not update_response.data:
             # Attempt to delete token even if user update fails, to prevent reuse
            db.table("user_login_token").update({"token": None}).eq("token", token).execute()
            raise ValueError("Failed to update password.")

        # 5. Invalidate or delete the used token from user_login_token
        (
            db.table("user_login_token")
            .update({"token": None})
            .eq("token", token)
            .execute()
        )

        return True # Indicate success

    except ValueError as ve:
        raise ve
    except Exception as e:
        print("Error in change_password",e)
        raise ValueError("Failed to process password change request. Please try again later.")
    
async def login(
    db:any,
    # subdomain:str,
    request: LoginRequest,
)->LoginSuccess:
    try:
        response = (
            db.table("user_tenant")
            .select("*")
            .or_("username.eq.{},email.eq.{}".format(request.email, request.email))
            .execute()
        )
        user_data = response.data[0]
        
        # Debug logs for hash comparison
        generated_hash = validated_user_password(
            user_data["password"],
            request.password
        )
        if generated_hash:
            # Generate random token with uppercase letters and numbers
            token_length = 6
            random_token = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(token_length))
            
            # await send_login_token(
            #     email_to=user_data["email"], 
            #     body={
            #         "email": user_data["email"], 
            #         "token": random_token
            #         }
            #     )
            # Update token_login in user tenant table
            update_response = (
                db.table("user_tenant")
                .update({"token_login": random_token})
                .eq("user_id", user_data["user_id"])
                .execute()
            )
            if not update_response.data:
                raise ValueError("Failed to update login token")
            # Insert token and exp time into user_login_token
            insert_data = {
                "user_id": user_data["user_id"],
                "token": random_token,
                "exp_datetime": (datetime.now() + timedelta(minutes=5)).isoformat(),
                "created_at": datetime.now().isoformat(),
            }
            token_insert_response = (
                db.table("user_login_token")
                .insert(insert_data)
                .execute()
            )
            if not update_response.data:
                raise ValueError("Failed to update login token")
            return user_data
        else:
            raise ValueError("Invalid username or password.")
    # except ValueError as ve:
    #     raise ve
    except Exception as e:
        print("Error login \n",e)
        raise ValueError("Invalid username or password.")


async def refresh_token_login(
    db:any,
    user:any
)->LoginSuccess:
    try:
        # Generate random token with uppercase letters and numbers
        token_length = 6
        random_token = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(token_length))
        # Update token_login in user tenant table
        update_response = (
            db.table("user_tenant")
            .update({"token_login": random_token})
            .eq("user_id", user["user_id"])
            .execute()
        )

        insert_data = {
            "user_id": user["user_id"],
            "token": random_token,
            "exp_datetime": (datetime.now() + timedelta(minutes=5)).isoformat(),
            "created_at": datetime.now().isoformat(),
        }
        token_insert_response = (
            db.table("user_login_token")
            .insert(insert_data)
            .execute()
        )
        
        if not update_response.data:
            raise ValueError("Failed to update login token")
        
        await send_login_token(
            email_to=user["email"], 
            body={
                "email": user["email"], 
                "token": random_token
                }
            )
        return "oke"
    except ValueError as ve:
        raise ve
    except Exception as e:
        print("Error refresh_token_login",e)
        raise ValueError("Login Failed")

async def check_login_token(
    db:any,
    user_id:str,
    token:str
):
    try:
        response = (
            db.table("user_login_token")
            .select("*")
            .eq("user_id", user_id)
            .eq("token", token)
            .execute()
        )
        if not response.data:
            raise ValueError("Invalid token")
        else:
            # Check if the token has expired
            token_data = response.data[0]
            if "exp_datetime" in token_data and datetime.fromisoformat(token_data["exp_datetime"]) < datetime.now():
                raise ValueError("Token has expired")
            # Update token_login to None after successful login
            update_response = (
                db.table("user_login_token")
                .update({"token": None})
                .eq("user_id", user_id)
                .execute()
            )
            if not update_response.data:
                raise ValueError("Failed to update token_login")
        
        # check login token in user_tenant table
        response = (
            db.table("user_tenant")
            .select("*")
            .eq("user_id", user_id)
            .eq("token_login", token)
            .execute()
        )
        if not response.data:
            raise ValueError("Invalid token")
        else:
            # Update token_login to None after successful login
            update_response = (
                db.table("user_tenant")
                .update({"token_login": None})
                .eq("user_id", user_id)
                .execute()
            )
            if not update_response.data:
                raise ValueError("Failed to update token_login")
        return "oke"
    except ValueError as ve:
        raise ve
    except Exception as e:
        print("Error check_login_token",e)
        raise ValueError(str(e))
    

async def get_user_by_email(
    db: AsyncSession, email: str, exclude_soft_delete: bool = False
) -> Optional[User]:
    try:
        if exclude_soft_delete == True:
            query = select(User).filter(User.email == email, User.isact == True)
        else:
            query = select(User).filter(User.email == email)
        results = await db.execute(query)
        user = results.scalar()
        return user
    except Exception as e:
        print("Error login : ",e)
        traceback.print_exc()
        return None

async def check_user_password(db: AsyncSession, email: str, password: str) -> Optional[User]:
    try:
        user = await get_user_by_email(db, email=email)
        if user is None:
            return None
        else:
            if validated_user_password(user.password, password):
                return user
        return None
    except Exception as e:
        print("Error in check_user_password:", e)
        traceback.print_exc()
        return None

    
async def edit_password(
    db:any,
    request: EditPassRequest,
):
    request.password = generate_hash_password(request.password)
    try:
        response = (
            db.table("users")
            .update({"password":request.password})
            .eq("email",request.email)
            .execute()
            )
        if response.data == []:
            raise ValueError("User not found")            
        return "Success"
    except Exception  as e:
        raise ValueError(str(e))
    
async def list_user(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    src: Optional[str] = None,
):
    try:
        limit = page_size
        offset = (page - 1) * limit

        query = select(User.id, User.name).filter(User.isact == True)
        query_count = select(func.count(User.id)).filter(User.isact == True)

        if src:
            query = query.filter(User.name.ilike(f"%{src}%"))
            query_count = query_count.filter(User.name.ilike(f"%{src}%"))

        query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        rows = await result.all() 

        data = [{"id": row.id, "name": row.name} for row in rows]

        count_result = await db.execute(query_count)
        num_data = await count_result.scalar() 
        num_page = (num_data + limit - 1) // limit

        return (data, num_data, num_page)

    except Exception as e:
        raise ValueError(e)

async def get_user_by_id(
    db: AsyncSession,
    user_id: str,
) -> Optional[User]:
    try:
        query = select(User).filter(
            User.id == user_id,
            User.isact == True
        ).options(
            selectinload(User.roles)
        )
        
        result = await db.execute(query)
        user = await result.scalar_one_or_none()
        
        return user

    except Exception as e:
        raise ValueError(e)

async def edit_user(
    db: AsyncSession,
    user_id: str,
    request: EditUserRequest,
) -> Optional[User]:
    try:
        user = await get_user_by_id(db=db, user_id=user_id)
        if not user:
            return None

        if request.name is not None:
            user.name = request.name
        if request.phone is not None:
            user.phone = request.phone
        if request.address is not None:
            user.address = request.address
        if request.isact is not None:
            user.isact = request.isact

        if request.role_id is not None:
            user.roles = []
            
            role_query = select(Role).filter(Role.id == request.role_id, Role.isact == True)
            role_result = await db.execute(role_query)
            new_role = await role_result.scalar_one_or_none()
            
            if new_role:
                user.roles.append(new_role)

        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user

    except Exception as e:
        traceback.print_exc()
        raise ValueError(str(e))

async def get_role_options(
    db: AsyncSession,
) -> List[Dict[str, Any]]:
    try:
        query = select(Role).filter(
            Role.isact == True
        ).order_by(Role.id.asc())

        result = await db.execute(query)
        roles = await result.scalars()

        role_options = [
            {
                "id": role.id,
                "name": role.name,
                "role" : role.group
            }
            for role in roles
        ]

        return role_options

    except Exception as e:
        traceback.print_exc()
        raise ValueError(str(e))

async def sign_up (
    db: AsyncSession,
    request: SignUpRequest,
):
    try:
        result = await db.execute(
            select(Role)
            .filter(Role.id == 1, Role.isact == True)
        )
        role = result.scalar()
        data =  User(
            email=request.email,
            password=generate_hash_password(request.password),
            name=request.name,
            phone=request.phone,
        )
        data.roles.append(role)
        db.add(data)
        await db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        raise ValueError(str(e))
