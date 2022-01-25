import random
import secrets
import string

whitespace = ' \t\n\r\v\f'
ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ascii_letters = ascii_lowercase + ascii_uppercase
digits = '0123456789'
hexdigits = digits + 'abcdef' + 'ABCDEF'
octdigits = '01234567'
# punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
punctuation = "!#$%&'()*+,-.:;<=>?@[]^_`{|}~"
printable = digits + ascii_letters + punctuation + whitespace


# secret_letters = string.digits + string.ascii_letters + string.punctuation
secret_letters = digits + ascii_letters + punctuation


def get_random_secret_key_bytes() -> bytes:
    return secrets.token_bytes(32)


def get_random_secret_key_str(n_bytes: int = 32) -> str:
    keys = []
    for i in range(n_bytes):
        keys.append(random.choice(secret_letters))
    return ''.join(keys)
