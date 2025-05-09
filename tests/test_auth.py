import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from repository.auth import (
    get_user_by_email,
    check_user_password,
    edit_password,
    list_user,
    get_user_by_id,
    edit_user,
    get_role_options,
    sign_up,
    forgot_password,
    change_password,
    login,
    check_login_token,
    refresh_token_login,
    logout_user
)
from models.User import User
from models.Role import Role
from schemas.auth import (
    EditPassRequest,
    EditUserRequest,
    SignUpRequest,
    LoginRequest
)

class TestAuth(unittest.IsolatedAsyncioTestCase):
    async def test_get_user_by_email_success(self):
        # Setup mock
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = User(
            id=1,
            email="test@example.com",
            name="Test User",
            isact=True
        )
        
        # Setup mock behavior
        mock_result = MagicMock()
        mock_result.scalar = Mock(return_value=mock_user)
        mock_db.execute.return_value = mock_result
        
        # Call function
        user = await get_user_by_email(mock_db, "test@example.com")
        
        # Assertions
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.name, "Test User")
        mock_db.execute.assert_called_once()

    @patch("repository.auth.validated_user_password")
    async def test_check_user_password_success(self, mock_validate):
        # Setup mocks
        mock_db = AsyncMock(spec=AsyncSession)
        mock_validate.return_value = True
        mock_user = User(
            id=1,
            email="test@example.com",
            password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBAQHxJ5Gq8K8y", # hashed "password123"
            isact=True
        )
        
        # Setup mock behavior
        mock_result = MagicMock()
        mock_result.scalar = Mock(return_value=mock_user)
        mock_db.execute.return_value = mock_result

        # Call function
        result = await check_user_password(mock_db, "test@example.com", "password123")

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result.email, "test@example.com")
        mock_db.execute.assert_called_once()
        mock_validate.assert_called_once_with(mock_user.password, "password123")

    async def test_edit_password_success(self):
        # Setup mock
        mock_db = MagicMock()
        mock_response = AsyncMock()
        
        # Mock data
        request = EditPassRequest(
            email="test@example.com",
            password="newpassword123",
            confirm_password="newpassword123"
        )
        mock_response.data = [{"email": "test@example.com"}]
        
        # Setup mock behavior
        mock_db.table().update().eq().execute.return_value = mock_response
        
        # Call function
        result = await edit_password(mock_db, request)
        
        # Assertions
        self.assertEqual(result, "Success")
        mock_db.table().update().eq().execute.assert_called_once()

    async def test_list_user_success(self):
        # Setup mock
        mock_db = AsyncMock(spec=AsyncSession)
        mock_users = [
            User(id=1, name="User 1"),
            User(id=2, name="User 2")
        ]
        
        # Setup mock behavior
        mock_db.execute.return_value.all.return_value = mock_users
        mock_db.execute.return_value.scalar.return_value = 2
        
        # Call function
        users, total, pages = await list_user(mock_db, page=1, page_size=10)
        
        # Assertions
        self.assertEqual(len(users), 2)
        self.assertEqual(total, 2)
        self.assertEqual(pages, 1)
        mock_db.execute.assert_called()

    async def test_get_user_by_id_success(self):
        # Setup mock
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = User(
            id=1,
            email="test@example.com",
            name="Test User",
            isact=True
        )
        
        # Setup mock behavior
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        # Call function
        user = await get_user_by_id(mock_db, "1")
        
        # Assertions
        self.assertIsNotNone(user)
        self.assertEqual(user.id, 1)
        self.assertEqual(user.email, "test@example.com")
        mock_db.execute.assert_called_once()

    async def test_edit_user_success(self):
        # Setup mock
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = User(
            id=1,
            email="test@example.com",
            name="Test User",
            isact=True
        )
        mock_role = Role(id=1, name="Admin", isact=True)

        # Create mock result object for db.execute
        mock_execute_result_1 = MagicMock()
        mock_execute_result_1.scalar_one_or_none = AsyncMock(return_value=mock_role)

        mock_execute_result_2 = MagicMock()
        mock_execute_result_2.scalar_one_or_none = AsyncMock(return_value=mock_user)

        # db.execute should return mock results in order (get_user_by_id, then role)
        mock_db.execute = AsyncMock(side_effect=[mock_execute_result_2, mock_execute_result_1])

        # Call function
        request = EditUserRequest(
            name="Updated User",
            phone="1234567890",
            address="New Address",
            isact=True,
            role_id=1
        )

        updated_user = await edit_user(mock_db, "1", request)

        # Assertions
        assert updated_user is not None
        assert updated_user.name == "Updated User"
        assert updated_user.phone == "1234567890"
        assert updated_user.roles[0].id == 1
    
    async def test_get_role_options_success(self):
        # Setup mock
        mock_db = AsyncMock(spec=AsyncSession)
        mock_roles = [
            Role(id=1, name="Admin", group="admin", isact=True),
            Role(id=2, name="User", group="user", isact=True)
        ]
        
        # Setup mock behavior
        mock_db.execute.return_value.scalars.return_value = mock_roles
        
        # Call function
        roles = await get_role_options(mock_db)
        
        # Assertions
        self.assertEqual(len(roles), 2)
        self.assertEqual(roles[0]["name"], "Admin")
        self.assertEqual(roles[1]["name"], "User")
        mock_db.execute.assert_called_once()

    async def test_sign_up_success(self):
        # Setup mock
        mock_db = AsyncMock(spec=AsyncSession)
        mock_role = Role(id=1, name="User", isact=True)
        
        mock_db.execute.return_value.scalar = Mock(return_value=mock_role)
        
        # Call function
        request = SignUpRequest(
            email="new@example.com",
            password="password123",
            name="New User",
            phone="1234567890"
        )
        result = await sign_up(mock_db, request)
        
        # Assertions
        self.assertTrue(result)
        mock_db.execute.assert_called_once()
        mock_db.add.assert_called_once()  
        mock_db.commit.assert_called_once()
        
    async def test_forgot_password_success(self):
        # Setup mock
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = User(
            id=1,
            email="test@example.com",
            isact=True
        )

        # Mock result of `execute().scalar()`
        mock_result = AsyncMock()
        mock_result.scalar.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Call function
        result = await forgot_password(mock_db, "test@example.com")

        # Assertions
        self.assertTrue(result)
        mock_db.execute.assert_called_once()

    async def test_change_password_success(self):
        # Setup mock
        mock_db = MagicMock()
        mock_response = AsyncMock()
        
        # Mock data
        mock_response.data = [{
            "user_id": "1",
            "exp_datetime": (datetime.now() + timedelta(minutes=5)).isoformat()
        }]
        
        # Setup mock behavior
        mock_db.table().select().eq().execute.return_value = mock_response
        mock_db.table().update().eq().execute.return_value = mock_response
        
        # Call function
        result = await change_password(mock_db, "valid_token", "newpassword123")
        
        # Assertions
        self.assertTrue(result)
        mock_db.table().select().eq().execute.assert_called_once()
        mock_db.table().update().eq().execute.assert_called()

    @patch("repository.auth.validated_user_password")
    async def test_login_success(self, mock_validate):
        # Setup mock
        mock_db = MagicMock()
        mock_response = AsyncMock()
        
        # Mock data
        mock_response.data = [{
            "user_id": "1",
            "email": "test@example.com",
            "password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBAQHxJ5Gq8K8y" # hashed "password123"
        }]
        
        # Setup mock behavior
        mock_validate.return_value = True
        mock_db.table().select().or_().execute.return_value = mock_response
        mock_db.table().update().eq().execute.return_value = mock_response
        mock_db.table().insert().execute.return_value = mock_response
        
        # Call function
        request = LoginRequest(
            email="test@example.com",
            password="password123"
        )
        result = await login(mock_db, request)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["email"], "test@example.com")
        mock_db.table().select().or_().execute.assert_called_once()
        mock_validate.assert_called_once()

    async def test_logout_user_success(self):
        # Setup mock
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = User(
            id=1,
            email="test@example.com",
            isact=True
        )
        
        # Create mock UserToken object
        mock_user_token = MagicMock()
        mock_user_token.isact = True
        
        # Setup mock behavior
        mock_result = AsyncMock()
        mock_result.scalar = AsyncMock(return_value=mock_user_token)
        mock_db.execute.return_value = mock_result
        
        # Call function
        result = await logout_user(mock_db, mock_user, "valid_token")
        
        # Assertions
        self.assertEqual(result, "oke")
        mock_db.execute.assert_called_once()
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once() 