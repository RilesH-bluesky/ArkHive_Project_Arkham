import os
from cryptography.fernet import Fernet

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(BASE_DIR, "secret.key")

def generate_key():
    key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as key_file:  # ← use KEY_PATH
        key_file.write(key)

def load_key():
    with open(KEY_PATH, "rb") as key_file:  # ← use KEY_PATH
        return key_file.read()

def encrypt_message(message: str, key: bytes) -> str:
    fernet = Fernet(key)
    return fernet.encrypt(message.encode()).decode()

def decrypt_message(token: str, key: bytes) -> str:
    fernet = Fernet(key)
    return fernet.decrypt(token.encode()).decode()