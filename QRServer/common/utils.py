import hashlib


def is_guest(username: str, password: bytes):
    return username.endswith(' GUEST') and \
           password == hashlib.md5(b'<NOPASS>').hexdigest().encode('ascii')
