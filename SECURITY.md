# Security Considerations

## Overview

This document outlines security considerations for the Fever Django implementation, particularly regarding API compatibility requirements vs. modern security best practices.

## Password Storage and Authentication

### Django Password Hashing (Secure)
User passwords are stored using Django's secure password hashing system:
- Uses PBKDF2 with SHA256 by default
- Includes salt and multiple iterations
- Industry-standard secure password storage
- Passwords are **never** stored in plain text

### Fever API Key (Compatibility Requirement)
The Fever API specification requires API keys in the format:
```
api_key = md5(email:password)
```

**Important Notes:**
- MD5 is used **only** for API key generation, not password storage
- This is required for backward compatibility with Fever API v3
- The API key is stored in the `fever_api_key` field for fast lookup
- This matches the original PHP Fever implementation

**Security Implications:**
- If an attacker gains access to the database, they could potentially derive passwords from API keys through rainbow tables or brute force
- This is a limitation of the Fever API specification, not our implementation
- The original PHP Fever had the same limitation

**Mitigation:**
1. **Use HTTPS** - Always use SSL/TLS in production to prevent API key interception
2. **Database Security** - Secure your database with proper access controls
3. **Strong Passwords** - Encourage users to use strong, unique passwords
4. **Network Security** - Run on a secure network with proper firewall rules
5. **Consider Token-Based Auth** - For new implementations, consider extending with JWT or OAuth2 (not Fever-compatible but more secure)

## Known Security Issues from CodeQL

### 1. MD5 for API Key Generation (By Design)
**Alert:** `py/weak-sensitive-data-hashing`
**Location:** `api/models.py` (lines 14, 37)

**Status:** ✅ Acknowledged - Required for Fever API compatibility

**Explanation:**
- MD5 is used for Fever API key generation per specification
- User passwords are stored securely with Django's password hashing
- This is a known trade-off for API compatibility

**Recommendation:**
- Users should be aware of this limitation
- Use HTTPS in production
- Consider implementing an alternative, more secure API for new clients

### 2. Clear-Text Password Logging (Demo/Test Files)
**Alert:** `py/clear-text-logging-sensitive-data`
**Locations:** 
- `setup_demo.py` (demo setup script)
- `test_api.py` (test script)

**Status:** ✅ Acceptable - Demo and testing purposes only

**Explanation:**
- These files are for demonstration and testing
- Passwords shown are for demo accounts only
- Not used in production code

**Recommendation:**
- Do not use demo credentials in production
- These scripts should not be deployed to production servers

### 3. JavaScript Sanitization Issues (Legacy Code)
**Alerts:** 
- `js/incomplete-sanitization` in `static/js/reader.js`
- `js/incomplete-multi-character-sanitization` in `static/js/fever.js`
- `js/redos` in `static/js/fever.js`

**Status:** ⚠️ Legacy Code

**Explanation:**
- These are from the original PHP Fever frontend code
- Copied as-is for reference
- The Django backend implements proper security

**Recommendation:**
- If using the legacy frontend, review and update the JavaScript
- Consider implementing a modern frontend with React/Vue/Svelte
- For API-only use (with Reeder, etc.), these files are not used

## Production Security Checklist

When deploying to production:

### Django Settings
```python
# fever_django/settings.py

# REQUIRED IN PRODUCTION
DEBUG = False
SECRET_KEY = 'your-secure-random-key-here'  # Change this!
ALLOWED_HOSTS = ['yourdomain.com']

# HTTPS Configuration
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

### Server Configuration
- ✅ Use HTTPS (SSL/TLS certificate from Let's Encrypt or similar)
- ✅ Use a production WSGI server (Gunicorn, uWSGI)
- ✅ Use a reverse proxy (Nginx, Apache)
- ✅ Enable firewall rules
- ✅ Keep software updated

### Database Security
- ✅ Use PostgreSQL or MySQL in production (not SQLite)
- ✅ Use strong database passwords
- ✅ Restrict database access to application server only
- ✅ Regular backups
- ✅ Enable database SSL connections

### User Management
- ✅ Enforce strong password policies
- ✅ Limit failed login attempts (consider django-axes)
- ✅ Monitor for suspicious activity
- ✅ Regular security audits
- ✅ Keep user list minimal

### Monitoring
- ✅ Set up logging (Django's logging framework)
- ✅ Monitor for failed authentication attempts
- ✅ Set up alerts for unusual activity
- ✅ Regular log reviews

## API Security

### Authentication
- API key required for all operations
- Rate limiting recommended (django-ratelimit)
- Monitor for brute force attempts

### HTTPS Requirement
**CRITICAL:** Always use HTTPS in production. HTTP transmits API keys in plain text.

### CSRF Protection
- POST requests include CSRF tokens
- API endpoint is exempt from CSRF (as per Fever spec)
- Web interface uses CSRF protection

## Responsible Disclosure

If you discover a security vulnerability:
1. **DO NOT** open a public issue
2. Email the maintainer directly
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Updates

Stay informed:
- Watch this repository for security updates
- Subscribe to Django security announcements
- Keep dependencies updated: `uv sync --upgrade`

## Alternative Authentication (Future)

For those who want better security than the Fever API provides, consider:
- Implementing OAuth2 authentication
- Using JWT tokens with refresh tokens
- Adding 2FA support
- Creating a GraphQL API with modern auth

These would not be Fever-compatible but would provide better security for modern clients.

## Conclusion

This implementation maintains compatibility with the Fever API v3 specification, which has inherent security limitations due to MD5 API keys. For production use:
1. **Always use HTTPS**
2. Implement proper server security
3. Use strong passwords
4. Monitor for suspicious activity
5. Consider the security trade-offs of API compatibility

For new implementations not requiring Fever compatibility, consider more secure modern authentication methods.
