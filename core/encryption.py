#!/usr/bin/env python3

import json
import os
import random
import string
import sys
import hashlib
import binascii
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from settings import ENCRYPTION_KEY


def encrypt_value(value, password=ENCRYPTION_KEY, salt=None):
    if salt is None:
        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=len("bocahngapayak098"))).encode('utf-8')
        # salt = "bocahngapayak098".encode('utf-8')
    elif isinstance(salt, str):
        salt = salt.encode('utf-8')

    # Derive key from password and salt
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000, 32)

    # Generate IV
    iv = os.urandom(16)

    # Create cipher
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()

    # Pad data (PKCS7)
    block_size = 16
    padding = block_size - (len(value) % block_size)
    padded_value = value + chr(padding) * padding

    # Encrypt
    encrypted = encryptor.update(padded_value.encode('utf-8')) + encryptor.finalize()

    result = binascii.hexlify(salt + iv + encrypted).decode('ascii')
    return f"{result}"

def decrypt_value(encrypted_hex, password=ENCRYPTION_KEY):
    try:
        encrypted_bytes = binascii.unhexlify(encrypted_hex)
        salt = encrypted_bytes[:len("bocahngapayak098")]
        iv = encrypted_bytes[len("bocahngapayak098"):len("bocahngapayak098")+16]
        encrypted = encrypted_bytes[len("bocahngapayak098")+16:]

        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000, 32)
        backend = default_backend()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
        decryptor = cipher.decryptor()
        padded_value = decryptor.update(encrypted) + decryptor.finalize()

        # Remove PKCS7 padding
        padding_len = padded_value[-1]
        value = padded_value[:-padding_len].decode('utf-8')
        return value
    except Exception as e:
        return encrypted_hex