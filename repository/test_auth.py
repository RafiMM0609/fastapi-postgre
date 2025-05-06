from datetime import datetime, timedelta
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from schemas.auth import EditPassRequest, LoginRequest, OtpRequest, SignupRequest
from repository.auth import check_exist_user, check_login_token, check_user_password, edit_password, get_id_tenant, get_list_emp_id, list_user, login, refresh_token_login, regis, verify_otp
import pytest

class TestAuth(unittest.IsolatedAsyncioTestCase):
    
    # Test login
    @patch("repository.auth.validated_user_password", return_value=True)
    @patch("repository.auth.send_login_token", new_callable=AsyncMock)
    async def test_login_success(self, mock_send_token, mock_validate_pw):
        # Setup MagicMock untuk db
        db = MagicMock()
        db.table().select().or_().execute.return_value.data = [{
            "user_id": 1,
            "email": "test@example.com",
            "password": "hashedpass"
        }]
        db.table().update().eq().execute.return_value.data = [{"token_login": "ABC123"}]
        db.table().insert().execute.return_value.data = [{"status": "inserted"}]

        # Buat request dummy
        request = LoginRequest(email="test@example.com", password="sigma")

        # Panggil fungsi login
        response = await login(db, request)

        # Assert hasilnya
        self.assertEqual(response["email"], "test@example.com")
        mock_send_token.assert_awaited_once()
        mock_validate_pw.assert_called_once_with("hashedpass", "sigma")
        
    @patch("repository.auth.validated_user_password", return_value=False)
    async def test_login_wrong_password(self, mock_validate_pw):
        db = MagicMock()
        db.table().select().or_().execute.return_value.data = [{
            "user_id": 1,
            "email": "test@example.com",
            "password": "hashedpass"
        }]
        request = LoginRequest(email="test@example.com", password="wrongpass")

        with self.assertRaises(ValueError) as context:
            await login(db, request)
        self.assertEqual(str(context.exception), "Invalid credentials")
        
    async def test_login_user_not_found(self):
        db = MagicMock()
        db.table().select().or_().execute.return_value.data = []
        request = LoginRequest(email="notfound@example.com", password="any")

        with self.assertRaises(ValueError) as context:
            await login(db, request)
        self.assertEqual(str(context.exception), "Login Failed")
        
    @patch("repository.auth.validated_user_password", return_value=True)
    @patch("repository.auth.send_login_token", new_callable=AsyncMock)
    async def test_login_update_token_failed(self, mock_send_token, mock_validate_pw):
        db = MagicMock()
        db.table().select().or_().execute.return_value.data = [{
            "user_id": 1,
            "email": "test@example.com",
            "password": "hashedpass"
        }]
        db.table().update().eq().execute.return_value.data = []  # Simulate gagal update
        request = LoginRequest(email="test@example.com", password="sigma")

        with self.assertRaises(ValueError) as context:
            await login(db, request)
        self.assertEqual(str(context.exception), "Failed to update login token")
        
    @patch("repository.auth.validated_user_password")
    @patch("repository.auth.send_login_token")
    async def test_login_failed_update_token(self, mock_send_token, mock_validate_password):
        db = MagicMock()

        # Step 1: User exists
        db.table().select().or_().execute.return_value.data = [{
            "email": "test@example.com",
            "password": "hashed_password",
            "user_id": "1234"
        }]

        # Step 2: Update gagal (biar masuk ke baris 'raise ValueError(...)')
        db.table().update().eq().execute.return_value.data = None

        # Run
        with pytest.raises(ValueError, match="Failed to update login token"):
            await login(db, LoginRequest(email="test@example.com", password="any_password"))


        
    # refresh token    
    @patch("repository.auth.send_login_token", new_callable=AsyncMock)
    async def test_refresh_token_success(self, mock_send_token):
        db = MagicMock()
        db.table().update().eq().execute.return_value.data = [{"token_login": "ABC123"}]

        user = {
            "user_id": 1,
            "email": "test@example.com"
        }

        result = await refresh_token_login(db, user)
        self.assertEqual(result, "oke")
        mock_send_token.assert_awaited_once_with(
            email_to="test@example.com",
            body={"email": "test@example.com", "token": unittest.mock.ANY}
        )
        
    async def test_refresh_token_failed_update(self):
        db = MagicMock()
        db.table().update().eq().execute.return_value.data = []

        user = {
            "user_id": 1,
            "email": "test@example.com"
        }

        with self.assertRaises(ValueError) as context:
            await refresh_token_login(db, user)
        self.assertEqual(str(context.exception), "Failed to update login token")
        
    # Check login token
    async def test_check_login_token_success(self):
        db = MagicMock()
        db.table().select().eq().eq().execute.return_value.data = [{"user_id": "1", "token_login": "ABC123"}]
        db.table().update().eq().execute.return_value.data = [{"token_login": None}]

        result = await check_login_token(db, "1", "ABC123")
        self.assertEqual(result, "oke")
        
    async def test_check_login_token_invalid(self):
        db = MagicMock()
        db.table().select().eq().eq().execute.return_value.data = []

        with self.assertRaises(ValueError) as context:
            await check_login_token(db, "1", "INVALID")
        self.assertEqual(str(context.exception), "Invalid token")
        
    async def test_check_login_token_update_failed(self):
        db = MagicMock()
        db.table().select().eq().eq().execute.return_value.data = [{"user_id": "1", "token_login": "ABC123"}]
        db.table().update().eq().execute.return_value.data = []

        with self.assertRaises(ValueError) as context:
            await check_login_token(db, "1", "ABC123")
        self.assertEqual(str(context.exception), "Failed to update token_login")

    # Get Id Tenant
    async def test_get_id_tenant_success(self):
        db = MagicMock()
        db.table().select().eq().execute.return_value.data = [{"id": "tenant123"}]

        result = await get_id_tenant(db, "subdomain-a")
        self.assertEqual(result, "tenant123")
        
    async def test_get_id_tenant_failed(self):
        db = MagicMock()
        db.table().select().eq().execute.return_value.data = []

        with self.assertRaises(ValueError) as context:
            await get_id_tenant(db, "subdomain-x")
        self.assertIn("list index out of range", str(context.exception))  # karena response.data[0]


    # Get List Emp Id
    async def test_get_list_emp_id_success(self):
        db = MagicMock()
        db.table().select().eq().execute.return_value.data = [
            {"id_user": "user1"},
            {"id_user": "user2"}
        ]

        result = await get_list_emp_id(db, "subdomain-a", "tenant123")
        self.assertEqual(result, [{"id_user": "user1"}, {"id_user": "user2"}])
        
    async def test_get_list_emp_id_failed(self):
        db = MagicMock()
        db.table().select().eq().execute.side_effect = Exception("DB Error")

        with self.assertRaises(ValueError) as context:
            await get_list_emp_id(db, "subdomain-a", "tenant123")
        self.assertIn("DB Error", str(context.exception))
        
    # Check User Password
    @patch("repository.auth.validated_user_password")
    def test_check_user_password_success(self, mock_validate):
        db = MagicMock()
        db.table().select().or_().execute.return_value.data = [{
            "email": "test@example.com",
            "password": "hashedpassword"
        }]
        mock_validate.return_value = True

        result = check_user_password(db, "test@example.com", "plainpassword")
        self.assertEqual(result["email"], "test@example.com")
        
    @patch("repository.auth.validated_user_password")
    def test_check_user_password_invalid_password(self, mock_validate):
        db = MagicMock()
        db.table().select().or_().execute.return_value.data = [{
            "email": "test@example.com",
            "password": "hashedpassword"
        }]
        mock_validate.return_value = False

        with self.assertRaises(ValueError) as context:
            check_user_password(db, "test@example.com", "wrongpass")
        self.assertEqual(str(context.exception), "Invalid credentical")
        
    def test_check_user_password_user_not_found(self):
        db = MagicMock()
        db.table().select().or_().execute.return_value.data = []

        with self.assertRaises(IndexError):
            check_user_password(db, "notfound@example.com", "any")
            
    # Check Exist User
    def test_check_exist_user_found(self):
        db = MagicMock()
        db.table().select().or_().execute.return_value.data = [{"user_id": "123"}]

        result = check_exist_user(db, "test@example.com", "testuser")
        self.assertTrue(result)
        
    def test_check_exist_user_not_found(self):
        db = MagicMock()
        db.table().select().or_().execute.return_value.data = []

        result = check_exist_user(db, "notfound@example.com", "nouser")
        self.assertFalse(result)
        
    def test_check_exist_user_exception(self):
        db = MagicMock()
        db.table().select().or_().execute.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            check_exist_user(db, "test@example.com", "testuser")
            
    # Regis
    @patch("repository.auth.check_exist_user", return_value=False)
    async def test_regis_success(self, mock_check_exist):
        db = MagicMock()
        db.table().insert().execute.return_value.data = [{"user_id": "123"}]
        request = SignupRequest(
            email="test@example.com",
            username="testuser",
            password="mypassword",
            name="Test User",
            photo="http://example.com/photo.jpg",
            phone="081234567890"
        )

        response = await regis(db, request)
        self.assertEqual(response, "oke")
        
    @patch("repository.auth.check_exist_user", return_value=True)
    async def test_regis_user_already_exists(self, mock_check_exist):
        db = MagicMock()
        request = SignupRequest(
            email="test@example.com",
            username="testuser",
            password="mypassword",
            name="Test User",
            photo="http://example.com/photo.jpg",
            phone="081234567890"
        )

        with self.assertRaises(ValueError) as context:
            await regis(db, request)
        self.assertEqual(str(context.exception), "User already exists")
        
    @patch("repository.auth.check_exist_user", return_value=False)
    async def test_regis_insert_failed(self, mock_check_exist):
        db = MagicMock()
        db.table().insert().execute.side_effect = Exception("Insert failed")
        request = SignupRequest(
            email="test@example.com",
            username="testuser",
            password="mypassword",
            name="Test User",
            photo="http://example.com/photo.jpg",
            phone="081234567890"
        )

        with self.assertRaises(ValueError) as context:
            await regis(db, request)
        self.assertIn("Registration failed", str(context.exception))
        
    # Edit Password
    async def test_edit_password_success(self):
        db = MagicMock()
        db.table().update().eq().execute.return_value.data = [{"email": "test@example.com"}]

        request = EditPassRequest(
            email="test@example.com",
            password="newpassword",
            confirm_password="newpassword"
        )

        result = await edit_password(db, request)
        self.assertEqual(result, "Success")
        
    async def test_edit_password_user_not_found(self):
        db = MagicMock()
        db.table().update().eq().execute.return_value.data = []

        request = EditPassRequest(
            email="notfound@example.com",
            password="newpassword",
            confirm_password="newpassword"
        )

        with self.assertRaises(ValueError) as context:
            await edit_password(db, request)
        self.assertEqual(str(context.exception), "User not found")
        
    async def test_edit_password_db_exception(self):
        db = MagicMock()
        db.table().update().eq().execute.side_effect = Exception("DB error")

        request = EditPassRequest(
            email="test@example.com",
            password="newpassword",
            confirm_password="newpassword"
        )

        with self.assertRaises(ValueError) as context:
            await edit_password(db, request)
        self.assertIn("DB error", str(context.exception))
        
    # List User
    async def test_list_user_success(self):
        db = MagicMock()
        dummy_data = [{"user_id": "1", "username": "user1"}, {"user_id": "2", "username": "user2"}]
        db.table().select().range().execute.return_value.data = dummy_data

        result, count = await list_user(db)

        self.assertEqual(result, dummy_data)
        self.assertEqual(count, 2)
        
    async def test_list_user_exception(self):
        db = MagicMock()
        db.table().select().range().execute.side_effect = Exception("DB error")

        from repository.auth import list_user
        with self.assertRaises(ValueError) as context:
            await list_user(db)

        self.assertIn("DB error", str(context.exception))
        
    # Verify OTP
    @patch("repository.auth.datetime", wraps=datetime)
    async def test_verify_otp_success(self, mock_datetime):
        db = MagicMock()
        now = datetime.utcnow()
        mock_datetime.utcnow.return_value = now

        db.table().select().eq().execute.return_value.data = [{
            "otp": "123456",
            "email": "test@example.com",
            "expires_at": now + timedelta(minutes=5),
        }]

        request = OtpRequest(email="test@example.com", otp="123456")
        result = await verify_otp(db, request)

        self.assertEqual(result, "OTP verified successfully")
        
    @patch("repository.auth.datetime", wraps=datetime)
    async def test_verify_otp_expired(self, mock_datetime):
        db = MagicMock()
        now = datetime.utcnow()
        mock_datetime.utcnow.return_value = now

        db.table().select().eq().execute.return_value.data = [{
            "otp": "123456",
            "email": "test@example.com",
            "expires_at": now - timedelta(minutes=1),
        }]

        from repository.auth import verify_otp, OtpRequest
        request = OtpRequest(email="test@example.com", otp="123456")
        
        with self.assertRaises(ValueError) as context:
            await verify_otp(db, request)
        self.assertIn("OTP has expired", str(context.exception))






