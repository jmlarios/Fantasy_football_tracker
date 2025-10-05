"""
Unit tests for the authentication service.

Tests password hashing, verification, user creation, and authentication.
"""

import pytest
from src.services.auth import AuthService
from src.models import User


class TestPasswordHashing:
    """Tests for password hashing functionality."""
    
    def test_hash_password_creates_hash(self):
        """Hashing a password should return a hash string."""
        password = "mysecurepassword123"
        password_hash = AuthService.hash_password(password)
        
        assert password_hash is not None
        assert isinstance(password_hash, str)
        assert len(password_hash) > 0
    
    def test_hash_password_not_plaintext(self):
        """Hash should not contain the original password."""
        password = "mysecurepassword123"
        password_hash = AuthService.hash_password(password)
        
        assert password not in password_hash
    
    def test_same_password_different_hashes(self):
        """Same password should produce different hashes (due to salt)."""
        password = "mysecurepassword123"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)
        
        assert hash1 != hash2  # Different salts make different hashes


class TestPasswordVerification:
    """Tests for password verification functionality."""
    
    def test_verify_correct_password(self):
        """Correct password should verify successfully."""
        password = "mysecurepassword123"
        password_hash = AuthService.hash_password(password)
        
        is_valid = AuthService.verify_password(password, password_hash)
        
        assert is_valid is True
    
    def test_verify_incorrect_password(self):
        """Incorrect password should fail verification."""
        password = "mysecurepassword123"
        wrong_password = "wrongpassword"
        password_hash = AuthService.hash_password(password)
        
        is_valid = AuthService.verify_password(wrong_password, password_hash)
        
        assert is_valid is False
    
    def test_verify_case_sensitive(self):
        """Password verification should be case-sensitive."""
        password = "MyPassword123"
        wrong_case = "mypassword123"
        password_hash = AuthService.hash_password(password)
        
        is_valid = AuthService.verify_password(wrong_case, password_hash)
        
        assert is_valid is False
    
    def test_verify_empty_password(self):
        """Empty password should not verify."""
        password = "mysecurepassword123"
        password_hash = AuthService.hash_password(password)
        
        is_valid = AuthService.verify_password("", password_hash)
        
        assert is_valid is False


class TestUserCreation:
    """Tests for user creation functionality."""
    
    def test_create_user_success(self, test_db):
        """Successfully create a new user."""
        # Arrange
        name = "New User"
        email = "newuser@example.com"
        password = "securepassword123"
        
        # Act
        user = AuthService.create_user(
            db=test_db,
            name=name,
            email=email,
            password=password
        )
        
        # Assert
        assert user is not None
        assert user.id is not None
        assert user.name == name
        assert user.email == email
        assert user.password_hash != password  # Should be hashed
        assert AuthService.verify_password(password, user.password_hash)  # Can verify
        assert user.is_active is True
    
    def test_create_user_duplicate_email(self, test_db):
        """Creating user with duplicate email should raise error."""
        # Arrange
        email = "duplicate@example.com"
        
        # Create first user
        AuthService.create_user(
            db=test_db,
            name="User 1",
            email=email,
            password="password1"
        )
        
        # Act & Assert - Second user with same email should fail
        with pytest.raises(ValueError, match="Email already registered"):
            AuthService.create_user(
                db=test_db,
                name="User 2",
                email=email,
                password="password2"
            )
    
    def test_create_user_password_is_hashed(self, test_db):
        """User password should be stored as hash, not plaintext."""
        password = "plaintext_password"
        
        user = AuthService.create_user(
            db=test_db,
            name="Test User",
            email="hashtest@example.com",
            password=password
        )
        
        # Password hash should not contain original password
        assert password not in user.password_hash
        assert user.password_hash.startswith("$2b$")  # bcrypt hash format


class TestUserAuthentication:
    """Tests for user authentication functionality."""
    
    def test_authenticate_user_success(self, test_db):
        """Authenticate user with correct credentials."""
        # Arrange - Create a user
        email = "auth@example.com"
        password = "correct_password"
        
        created_user = AuthService.create_user(
            db=test_db,
            name="Auth User",
            email=email,
            password=password
        )
        
        # Act - Authenticate with correct credentials
        authenticated_user = AuthService.authenticate_user(
            db=test_db,
            email=email,
            password=password
        )
        
        # Assert
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.email == email
    
    def test_authenticate_user_wrong_password(self, test_db):
        """Authentication should fail with wrong password."""
        # Arrange
        email = "wrongpass@example.com"
        correct_password = "correct123"
        wrong_password = "wrong456"
        
        AuthService.create_user(
            db=test_db,
            name="User",
            email=email,
            password=correct_password
        )
        
        # Act
        result = AuthService.authenticate_user(
            db=test_db,
            email=email,
            password=wrong_password
        )
        
        # Assert
        assert result is None
    
    def test_authenticate_user_nonexistent_email(self, test_db):
        """Authentication should fail for non-existent email."""
        result = AuthService.authenticate_user(
            db=test_db,
            email="nonexistent@example.com",
            password="anypassword"
        )
        
        assert result is None
    
    def test_authenticate_inactive_user(self, test_db):
        """Authentication should fail for inactive users."""
        # Arrange - Create and deactivate user
        email = "inactive@example.com"
        password = "password123"
        
        user = AuthService.create_user(
            db=test_db,
            name="Inactive User",
            email=email,
            password=password
        )
        
        # Deactivate user
        user.is_active = False
        test_db.commit()
        
        # Act
        result = AuthService.authenticate_user(
            db=test_db,
            email=email,
            password=password
        )
        
        # Assert
        assert result is None


class TestGetUserById:
    """Tests for get_user_by_id functionality."""
    
    def test_get_user_by_id_success(self, test_db):
        """Get user by ID should return correct user."""
        # Arrange
        user = AuthService.create_user(
            db=test_db,
            name="ID Test User",
            email="idtest@example.com",
            password="password123"
        )
        
        # Act
        found_user = AuthService.get_user_by_id(test_db, user.id)
        
        # Assert
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.email == user.email
    
    def test_get_user_by_id_not_found(self, test_db):
        """Get user by non-existent ID should return None."""
        result = AuthService.get_user_by_id(test_db, 99999)
        assert result is None
    
    def test_get_user_by_id_inactive_user(self, test_db):
        """Get user by ID should not return inactive users."""
        # Arrange
        user = AuthService.create_user(
            db=test_db,
            name="Inactive User",
            email="inactive_id@example.com",
            password="password123"
        )
        
        user_id = user.id
        
        # Deactivate
        user.is_active = False
        test_db.commit()
        
        # Act
        result = AuthService.get_user_by_id(test_db, user_id)
        
        # Assert
        assert result is None


class TestGetUserByEmail:
    """Tests for get_user_by_email functionality."""
    
    def test_get_user_by_email_success(self, test_db):
        """Get user by email should return correct user."""
        # Arrange
        email = "emailtest@example.com"
        user = AuthService.create_user(
            db=test_db,
            name="Email Test User",
            email=email,
            password="password123"
        )
        
        # Act
        found_user = AuthService.get_user_by_email(test_db, email)
        
        # Assert
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.email == email
    
    def test_get_user_by_email_not_found(self, test_db):
        """Get user by non-existent email should return None."""
        result = AuthService.get_user_by_email(test_db, "nonexistent@example.com")
        assert result is None
    
    def test_get_user_by_email_inactive_user(self, test_db):
        """Get user by email should not return inactive users."""
        # Arrange
        email = "inactive_email@example.com"
        user = AuthService.create_user(
            db=test_db,
            name="Inactive User",
            email=email,
            password="password123"
        )
        
        # Deactivate
        user.is_active = False
        test_db.commit()
        
        # Act
        result = AuthService.get_user_by_email(test_db, email)
        
        # Assert
        assert result is None


class TestPasswordEdgeCases:
    """Tests for password edge cases and security."""
    
    def test_password_with_special_characters(self, test_db):
        """Passwords with special characters should work."""
        password = "P@ssw0rd!#$%^&*()"
        
        user = AuthService.create_user(
            db=test_db,
            name="Special Char User",
            email="special@example.com",
            password=password
        )
        
        assert AuthService.verify_password(password, user.password_hash)
    
    def test_password_with_unicode(self, test_db):
        """Passwords with unicode characters should work."""
        password = "pässwörd123"
        
        user = AuthService.create_user(
            db=test_db,
            name="Unicode User",
            email="unicode@example.com",
            password=password
        )
        
        assert AuthService.verify_password(password, user.password_hash)
    
    def test_very_long_email(self, test_db):
        """User creation should handle long emails."""
        long_email = "a" * 50 + "@example.com"
        
        user = AuthService.create_user(
            db=test_db,
            name="Long Email User",
            email=long_email,
            password="password123"
        )
        
        assert user.email == long_email
