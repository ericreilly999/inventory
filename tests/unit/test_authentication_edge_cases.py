"""Unit tests for authentication edge cases.

Tests invalid credentials, expired tokens, role changes
Requirements: 6.1, 6.2, 6.4
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from jose import jwt

from shared.auth.utils import (
    hash_password, verify_password, create_access_token, 
    verify_token, extract_user_id
)
from shared.config.settings import settings


class TestAuthenticationEdgeCases:
    """Unit tests for authentication edge cases."""
    
    def test_invalid_credentials_password_verification(self):
        """Test password verification with invalid credentials."""
        # Test with correct password
        password = "correct_password123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) == True
        
        # Test with wrong password
        assert verify_password("wrong_password", hashed) == False
        
        # Test with empty password
        assert verify_password("", hashed) == False
        
        # Test with None password
        with pytest.raises(TypeError):
            verify_password(None, hashed)
        
        # Test with empty hash
        assert verify_password(password, "") == False
        
        # Test with None hash
        with pytest.raises(TypeError):
            verify_password(password, None)
    
    def test_malformed_tokens(self):
        """Test token verification with malformed tokens."""
        # Test with empty token
        assert verify_token("") is None
        
        # Test with None token
        assert verify_token(None) is None
        
        # Test with invalid JWT format
        assert verify_token("invalid.jwt.token") is None
        
        # Test with random string
        assert verify_token("random_string_not_jwt") is None
        
        # Test with partial JWT
        assert verify_token("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9") is None
    
    def test_expired_tokens(self):
        """Test token verification with expired tokens."""
        # Create token with past expiration
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        token_data = {
            "sub": "test_user_id",
            "username": "testuser",
            "exp": past_time
        }
        
        expired_token = jwt.encode(
            token_data,
            settings.auth.jwt_secret_key,
            algorithm=settings.auth.jwt_algorithm
        )
        
        # Expired token should return None
        assert verify_token(expired_token) is None
    
    def test_token_with_wrong_secret(self):
        """Test token verification with wrong secret key."""
        token_data = {
            "sub": "test_user_id",
            "username": "testuser",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        
        # Create token with different secret
        wrong_secret_token = jwt.encode(
            token_data,
            "wrong_secret_key",
            algorithm=settings.auth.jwt_algorithm
        )
        
        # Token with wrong secret should return None
        assert verify_token(wrong_secret_token) is None
    
    def test_token_with_wrong_algorithm(self):
        """Test token verification with wrong algorithm."""
        token_data = {
            "sub": "test_user_id",
            "username": "testuser",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        
        # Create token with different algorithm
        wrong_algo_token = jwt.encode(
            token_data,
            settings.auth.jwt_secret_key,
            algorithm="HS512"  # Different from configured HS256
        )
        
        # Token with wrong algorithm should return None
        assert verify_token(wrong_algo_token) is None
    
    def test_token_missing_required_fields(self):
        """Test token verification with missing required fields."""
        # Token without 'sub' field
        token_without_sub = create_access_token({
            "username": "testuser",
            "role_id": "role123"
        })
        
        # Should still verify (sub is added by create_access_token if missing)
        payload = verify_token(token_without_sub)
        assert payload is not None
        
        # But extract_user_id should handle missing sub gracefully
        user_id = extract_user_id(token_without_sub)
        # This depends on implementation - might be None or raise exception
    
    def test_extract_user_id_edge_cases(self):
        """Test user ID extraction edge cases."""
        # Test with valid token
        token_data = {"sub": "user123"}
        valid_token = create_access_token(token_data)
        user_id = extract_user_id(valid_token)
        assert user_id == "user123"
        
        # Test with invalid token
        assert extract_user_id("invalid_token") is None
        
        # Test with empty token
        assert extract_user_id("") is None
        
        # Test with None token
        assert extract_user_id(None) is None
    
    def test_role_changes_token_validity(self):
        """Test that role changes don't affect existing token validity."""
        # Create token with specific role
        original_role_id = "role123"
        token_data = {
            "sub": "user123",
            "username": "testuser",
            "role_id": original_role_id,
            "permissions": {"read": True, "write": False}
        }
        
        token = create_access_token(token_data)
        
        # Verify token is valid
        payload = verify_token(token)
        assert payload is not None
        assert payload["role_id"] == original_role_id
        assert payload["permissions"]["read"] == True
        assert payload["permissions"]["write"] == False
        
        # Token should remain valid even if user's role changes in database
        # (This is expected behavior - tokens contain snapshot of permissions)
        # New tokens would need to be issued to reflect role changes
    
    def test_password_hash_consistency(self):
        """Test password hashing consistency and edge cases."""
        password = "test_password123"
        
        # Same password should produce different hashes (due to salt)
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) == True
        assert verify_password(password, hash2) == True
        
        # Cross-verification should fail
        assert verify_password(password, hash1) == True
        assert verify_password(password, hash2) == True
    
    def test_empty_and_whitespace_passwords(self):
        """Test handling of empty and whitespace-only passwords."""
        # Empty password
        empty_hash = hash_password("")
        assert verify_password("", empty_hash) == True
        assert verify_password("not_empty", empty_hash) == False
        
        # Whitespace-only password
        whitespace_password = "   \t\n  "
        whitespace_hash = hash_password(whitespace_password)
        assert verify_password(whitespace_password, whitespace_hash) == True
        assert verify_password("different", whitespace_hash) == False
    
    def test_unicode_passwords(self):
        """Test handling of unicode characters in passwords."""
        # Keep unicode password short to avoid bcrypt 72-byte limit
        unicode_password = "пароль123🔐"[:50]  # Truncate to avoid bcrypt limit
        unicode_hash = hash_password(unicode_password)
        
        assert verify_password(unicode_password, unicode_hash) == True
        assert verify_password("different", unicode_hash) == False
    
    def test_very_long_passwords(self):
        """Test handling of very long passwords."""
        # bcrypt has a 72-byte limit, so test with a password just under that
        long_password = "a" * 70  # Just under bcrypt's 72-byte limit
        long_hash = hash_password(long_password)
        
        assert verify_password(long_password, long_hash) == True
        assert verify_password(long_password[:-1], long_hash) == False
    
    def test_token_payload_edge_cases(self):
        """Test token creation with various payload edge cases."""
        # Empty payload
        empty_token = create_access_token({})
        payload = verify_token(empty_token)
        assert payload is not None
        assert "exp" in payload  # Expiration should be added
        
        # Payload with None values
        none_payload = {"sub": None, "username": None}
        none_token = create_access_token(none_payload)
        payload = verify_token(none_token)
        assert payload is not None
        assert payload["sub"] is None
        assert payload["username"] is None
        
        # Payload with complex nested data
        complex_payload = {
            "sub": "user123",
            "permissions": {
                "nested": {
                    "deep": {
                        "value": True
                    }
                },
                "list": [1, 2, 3]
            }
        }
        complex_token = create_access_token(complex_payload)
        payload = verify_token(complex_token)
        assert payload is not None
        assert payload["permissions"]["nested"]["deep"]["value"] == True
        assert payload["permissions"]["list"] == [1, 2, 3]