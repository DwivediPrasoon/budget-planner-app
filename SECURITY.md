# Security & Encryption Documentation

## Overview

The Budget Planner application implements comprehensive encryption to protect user data from unauthorized access. This document explains the security measures in place.

## 🔐 Encryption Architecture

### Multi-Layer Security

1. **Password Hashing**: User passwords are hashed using PBKDF2 with SHA-256
2. **Data Encryption**: Sensitive transaction data is encrypted using Fernet (AES-128)
3. **Key Derivation**: User-specific encryption keys are derived from passwords using PBKDF2
4. **Salt Generation**: Unique salts are used for each user and each encryption operation

### What Data is Encrypted

- **Transaction Descriptions**: All transaction descriptions are encrypted
- **User Passwords**: Stored as PBKDF2 hashes with unique salts
- **Future Expansion**: System designed to easily encrypt additional fields

## 🔑 Key Management

### Master Encryption Key
- Stored in environment variable `ENCRYPTION_KEY`
- Generated automatically if not provided (development only)
- **IMPORTANT**: Set a strong encryption key in production

### User-Specific Keys
- Derived from user passwords using PBKDF2
- 100,000 iterations for key derivation
- Unique salt per user for additional security

### Key Derivation Process
```
User Password + Salt → PBKDF2 → User Encryption Key → Fernet Cipher
```

## 🛡️ Security Features

### Password Security
- **Algorithm**: PBKDF2 with SHA-256
- **Iterations**: 100,000 (industry standard)
- **Salt**: 16-byte random salt per user
- **Storage**: Only hash and salt stored, never plain passwords

### Data Encryption
- **Algorithm**: Fernet (AES-128 in CBC mode with HMAC)
- **Key Size**: 256-bit keys
- **IV**: Automatically generated for each encryption
- **Authentication**: HMAC prevents tampering

### Session Security
- User passwords temporarily stored in session for decryption
- Session data is encrypted by Flask
- Passwords cleared on logout

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,      -- PBKDF2 hash
    password_salt VARCHAR(255) NOT NULL,      -- Salt for password hashing
    encryption_salt VARCHAR(255),             -- Salt for data encryption
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT,                         -- Unencrypted (legacy)
    description_encrypted TEXT,               -- Encrypted description
    description_salt VARCHAR(255),            -- Salt for description encryption
    type VARCHAR(20) DEFAULT 'expense',
    payment_method VARCHAR(50) DEFAULT 'cash',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Implementation Details

### Encryption Process
1. User logs in with password
2. Password verified against stored hash
3. User-specific encryption key derived from password
4. Sensitive data encrypted before database storage
5. Data decrypted when retrieved for display

### Decryption Process
1. User password retrieved from session
2. User-specific key re-derived from password
3. Encrypted data decrypted using derived key
4. Plain text data returned to application

### Error Handling
- Decryption failures are handled gracefully
- Fallback to unencrypted data if available
- Logging of decryption errors for debugging

## 🚀 Production Deployment

### Environment Variables
```bash
# Required for production
ENCRYPTION_KEY=your-strong-encryption-key-here

# Database configuration
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=budget_planner
DB_USER=your-db-user
DB_PASSWORD=your-db-password
```

### Generating Encryption Key
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Use this as ENCRYPTION_KEY
```

### Security Checklist
- [ ] Set strong `ENCRYPTION_KEY` environment variable
- [ ] Use HTTPS in production
- [ ] Enable database SSL connections
- [ ] Regular security updates
- [ ] Monitor for suspicious activity
- [ ] Backup encryption keys securely

## 🔍 Security Best Practices

### For Users
- Use strong, unique passwords
- Never share passwords
- Log out when using shared devices
- Report suspicious activity

### For Developers
- Never log sensitive data
- Use environment variables for secrets
- Regular security audits
- Keep dependencies updated
- Follow OWASP guidelines

## 🛠️ Troubleshooting

### Common Issues

**Decryption Errors**
- Check if user password is correct
- Verify encryption key is set correctly
- Check database for corrupted data

**Migration Issues**
- Old data may be unencrypted
- New data will be encrypted automatically
- Gradual migration supported

### Debug Mode
- Encryption errors are logged
- Fallback mechanisms in place
- Graceful degradation for legacy data

## 📈 Future Enhancements

### Planned Security Features
- [ ] Field-level encryption for categories
- [ ] Encrypted backup/export
- [ ] Two-factor authentication
- [ ] Audit logging
- [ ] Data retention policies
- [ ] GDPR compliance tools

### Encryption Expansion
- [ ] Encrypt transaction categories
- [ ] Encrypt expected expense descriptions
- [ ] Encrypt user preferences
- [ ] Encrypted API responses

## 🔒 Compliance

### Data Protection
- User data encrypted at rest
- Secure transmission protocols
- Access controls implemented
- Audit trails available

### Privacy
- Minimal data collection
- User control over data
- Secure deletion options
- Transparency in data handling

## 📞 Security Contact

For security issues or questions:
- Review this documentation
- Check application logs
- Contact development team
- Report vulnerabilities responsibly

---

**Note**: This security implementation follows industry best practices and is designed to protect user data while maintaining usability. Regular security reviews and updates are recommended. 