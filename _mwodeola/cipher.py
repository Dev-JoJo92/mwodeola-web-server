import base64
from django.conf import settings

from Crypto import Random
from Crypto.Cipher import AES


SECRET_KEY_AES = settings.SECRET_KEY_AES.encode()
BS = 16
pad = lambda s: s + (BS - len(s.encode('utf-8')) % BS) * chr(BS - len(s.encode('utf-8')) % BS)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]


class AESCipher:
    def __init__(self, key=SECRET_KEY_AES):
        self.key = key
        # self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        if raw is None:
            return None
        else:
            raw = pad(raw)
            iv = Random.new().read(AES.block_size)
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            return base64.b64encode(iv + cipher.encrypt(raw.encode('utf-8'))).decode()
            # return base64.b64encode(iv + cipher.encrypt(raw.encode('utf-8')))

    def decrypt(self, enc):
        if enc is None:
            return None
        else:
            enc = base64.b64decode(enc)
            iv = enc[:16]
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            return unpad(cipher.decrypt(enc[16:])).decode()
            # return unpad(cipher.decrypt(enc[16:]))
