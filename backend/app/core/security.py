from cryptography.fernet import Fernet
from app.core.config import get_settings

def _get_fernet():
    key = get_settings().secret_key
    # Fernet requires 32 url-safe base64 bytes. 
    # If config secret is arbitrary, we hash it to fit.
    import base64
    import hashlib
    
    # Derive a reliable key from the secret
    digest = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(digest)
    return Fernet(fernet_key)

def encrypt_token(token: str) -> str:
    if not token: return token
    f = _get_fernet()
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token: return ""
    f = _get_fernet()
    try:
        return f.decrypt(encrypted_token.encode()).decode()
    except Exception:
        # Failed to decrypt (maybe old plain token?), return as is or error
        # For migration safety, returning as causes potential issues if not careful.
        # But here we assume fresh start.
        return ""
