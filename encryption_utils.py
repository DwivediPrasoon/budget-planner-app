"""
Encryption utilities for Budget Planner
Provides encryption/decryption for sensitive user data
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import secrets
import json
from typing import Optional, Dict, Any

class DataEncryption:
    """Handles encryption and decryption of sensitive user data"""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption with a master key
        
        Args:
            master_key: Master encryption key. If None, generates a new one.
        """
        if master_key:
            self.master_key = master_key.encode()
        else:
            # Generate a new master key
            self.master_key = Fernet.generate_key()
        
        self.fernet = Fernet(self.master_key)
    
    def generate_user_key(self, user_password: str, user_salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """
        Generate a unique encryption key for each user based on their password
        
        Args:
            user_password: User's password
            user_salt: Salt for key derivation. If None, generates a new one.
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if user_salt is None:
            user_salt = os.urandom(16)
        
        # Use PBKDF2 to derive a key from the user's password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=user_salt,
            iterations=100000,
            backend=default_backend()
        )
        
        derived_key = base64.urlsafe_b64encode(kdf.derive(user_password.encode()))
        return derived_key, user_salt
    
    def encrypt_user_data(self, data: str, user_password: str, user_salt: Optional[bytes] = None) -> Dict[str, str]:
        """
        Encrypt user data with a user-specific key
        
        Args:
            data: Data to encrypt
            user_password: User's password for key derivation
            user_salt: Salt for key derivation. If None, generates a new one.
            
        Returns:
            Dictionary containing encrypted data and salt
        """
        user_key, salt = self.generate_user_key(user_password, user_salt)
        user_fernet = Fernet(user_key)
        
        encrypted_data = user_fernet.encrypt(data.encode())
        
        return {
            'encrypted_data': base64.urlsafe_b64encode(encrypted_data).decode(),
            'salt': base64.urlsafe_b64encode(salt).decode()
        }
    
    def decrypt_user_data(self, encrypted_data: str, salt: str, user_password: str) -> str:
        """
        Decrypt user data with user-specific key
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            salt: Base64 encoded salt used for key derivation
            user_password: User's password for key derivation
            
        Returns:
            Decrypted data
        """
        try:
            salt_bytes = base64.urlsafe_b64decode(salt.encode())
            user_key, _ = self.generate_user_key(user_password, salt_bytes)
            user_fernet = Fernet(user_key)
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = user_fernet.decrypt(encrypted_bytes)
            
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    def encrypt_sensitive_field(self, value: str, user_password: str, user_salt: Optional[bytes] = None) -> Dict[str, str]:
        """
        Encrypt a single sensitive field (like transaction descriptions)
        
        Args:
            value: Field value to encrypt
            user_password: User's password
            user_salt: Salt for key derivation
            
        Returns:
            Dictionary with encrypted value and salt
        """
        if not value:
            return {'encrypted_data': '', 'salt': ''}
        
        return self.encrypt_user_data(value, user_password, user_salt)
    
    def decrypt_sensitive_field(self, encrypted_value: str, salt: str, user_password: str) -> str:
        """
        Decrypt a single sensitive field
        
        Args:
            encrypted_value: Encrypted field value
            salt: Salt used for encryption
            user_password: User's password
            
        Returns:
            Decrypted field value
        """
        if not encrypted_value or not salt:
            return ''
        
        return self.decrypt_user_data(encrypted_value, salt, user_password)

class DatabaseEncryption:
    """Handles database-level encryption operations"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize database encryption
        
        Args:
            encryption_key: Encryption key. If None, generates a new one.
        """
        self.encryption = DataEncryption(encryption_key)
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """
        Hash user password with salt
        
        Args:
            password: User password
            salt: Salt for hashing. If None, generates a new one.
            
        Returns:
            Dictionary with hashed password and salt
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use a strong hashing algorithm
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        hashed_password = hash_obj.hex()
        
        return {
            'hashed_password': hashed_password,
            'salt': salt
        }
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """
        Verify user password
        
        Args:
            password: Password to verify
            hashed_password: Stored hashed password
            salt: Salt used for hashing
            
        Returns:
            True if password is correct, False otherwise
        """
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_obj.hex() == hashed_password
    
    def encrypt_transaction_data(self, transaction_data: Dict[str, Any], user_password: str) -> Dict[str, Any]:
        """
        Encrypt sensitive transaction data
        
        Args:
            transaction_data: Transaction data dictionary
            user_password: User's password
            
        Returns:
            Transaction data with sensitive fields encrypted
        """
        encrypted_data = transaction_data.copy()
        
        # Encrypt sensitive fields
        sensitive_fields = ['description']
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_result = self.encryption.encrypt_sensitive_field(
                    str(encrypted_data[field]), 
                    user_password
                )
                encrypted_data[f'{field}_encrypted'] = encrypted_result['encrypted_data']
                encrypted_data[f'{field}_salt'] = encrypted_result['salt']
                # Remove original field
                encrypted_data.pop(field, None)
        
        return encrypted_data
    
    def decrypt_transaction_data(self, transaction_data: Dict[str, Any], user_password: str) -> Dict[str, Any]:
        """
        Decrypt sensitive transaction data
        
        Args:
            transaction_data: Transaction data with encrypted fields
            user_password: User's password
            
        Returns:
            Transaction data with decrypted fields
        """
        decrypted_data = transaction_data.copy()
        
        # Decrypt sensitive fields
        sensitive_fields = ['description']
        
        for field in sensitive_fields:
            encrypted_field = f'{field}_encrypted'
            salt_field = f'{field}_salt'
            
            if encrypted_field in decrypted_data and salt_field in decrypted_data:
                try:
                    decrypted_value = self.encryption.decrypt_sensitive_field(
                        decrypted_data[encrypted_field],
                        decrypted_data[salt_field],
                        user_password
                    )
                    decrypted_data[field] = decrypted_value
                except Exception as e:
                    # If decryption fails, use empty string
                    decrypted_data[field] = ''
                
                # Remove encrypted fields
                decrypted_data.pop(encrypted_field, None)
                decrypted_data.pop(salt_field, None)
        
        return decrypted_data

# Global encryption instance
db_encryption = DatabaseEncryption()

def get_encryption_key() -> str:
    """Get or generate encryption key from environment"""
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        # Generate a new key if not exists
        key = Fernet.generate_key().decode()
        print(f"⚠️  Generated new encryption key. Set ENCRYPTION_KEY environment variable for production.")
    return key

def initialize_encryption():
    """Initialize global encryption with proper key"""
    global db_encryption
    key = get_encryption_key()
    db_encryption = DatabaseEncryption(key) 