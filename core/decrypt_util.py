"""密码解密工具，兼容 encrypt_ 前缀的 Blowfish 加密密码"""

from Crypto.Cipher import Blowfish
from Crypto.Util.Padding import unpad
import base64


def _string_to_bytes(encrypted_str: str) -> bytes:
    encrypted_str = encrypted_str.strip()
    if len(encrypted_str) % 2 != 0:
        encrypted_str = '0' + encrypted_str

    try:
        return bytes.fromhex(encrypted_str)
    except ValueError:
        try:
            return base64.b64decode(encrypted_str)
        except Exception:
            return encrypted_str.encode('utf-8')


def _blowfish_decrypt(key: str, encrypted: str) -> str:
    key_bytes = key.encode('utf-8')
    cipher = Blowfish.new(key_bytes, Blowfish.MODE_ECB)
    encrypted_bytes = _string_to_bytes(encrypted)
    decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), Blowfish.block_size)
    return decrypted_bytes.decode('utf-8')


def decrypt_pwd(encrypted_text: str) -> str:
    """解密密码。如果以 'encrypt_' 开头则进行 Blowfish 解密，否则原样返回。"""
    if not encrypted_text:
        return encrypted_text
    key = "111111111111"
    if encrypted_text.startswith("encrypt_"):
        encrypted_text = encrypted_text[len("encrypt_"):]
        return _blowfish_decrypt(key, encrypted_text)
    return encrypted_text
