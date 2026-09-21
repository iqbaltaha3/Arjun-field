import hashlib, hmac, secrets

def hash_password(password, salt=None):
    salt=salt or secrets.token_hex(16)
    digest=hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120_000).hex()
    return f'{salt}${digest}'

def verify_password(password, stored):
    try:
        salt,digest=stored.split('$',1)
        check=hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120_000).hex()
        return hmac.compare_digest(check,digest)
    except Exception:
        return False
