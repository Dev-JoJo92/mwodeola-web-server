import random
import secrets
import string

secret_letters = string.digits + string.ascii_letters + string.punctuation


def get_random_secret_key_bytes() -> bytes:
    return secrets.token_bytes(32)


def get_random_secret_key_str(n_bytes: int = 32) -> str:
    keys = []
    for i in range(n_bytes):
        keys.append(random.choice(secret_letters))
    return ''.join(keys)
