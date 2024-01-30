import binascii
import hashlib
import os

_iterations = 100000
_hash_name = 'sha512'


def password_hash(password: bytes) -> str:
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    h = hashlib.pbkdf2_hmac(
        _hash_name,
        password,
        salt,
        _iterations)
    h = binascii.hexlify(h)
    return (salt + h).decode('ascii')


def password_verify(provided_password: bytes, stored_hash: str) -> bool:
    if not stored_hash or not provided_password:
        return False

    salt = stored_hash[:64]
    stored_hash = stored_hash[64:]
    h = hashlib.pbkdf2_hmac(
        _hash_name,
        provided_password,
        salt.encode('ascii'),
        _iterations)
    h = binascii.hexlify(h).decode('ascii')
    return h == stored_hash
