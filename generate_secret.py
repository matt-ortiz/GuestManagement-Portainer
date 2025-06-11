#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for Flask application
Run this script and copy the output to use in Portainer environment variables
"""

import secrets
import string

def generate_secret_key(length=32):
    """Generate a cryptographically secure secret key"""
    return secrets.token_urlsafe(length)

def generate_password(length=16):
    """Generate a secure password for other uses"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    print("🔐 Security Key Generator for Guest Management App")
    print("=" * 55)
    print()
    print("SECRET_KEY for Flask:")
    print(f"  {generate_secret_key()}")
    print()
    print("Alternative SECRET_KEY:")
    print(f"  {generate_secret_key()}")
    print()
    print("Sample secure password (for other uses):")
    print(f"  {generate_password()}")
    print()
    print("📋 Copy one of the SECRET_KEY values above and use it in Portainer")
    print("   Environment Variables section as: SECRET_KEY=your-key-here")
