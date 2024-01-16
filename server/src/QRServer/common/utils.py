import hashlib


def is_guest(username: str, password: str):
    return username.endswith(' GUEST') and \
           password == hashlib.md5(b'<NOPASS>').hexdigest()
