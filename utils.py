import bcrypt


def hash_passowrd(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hash):
    return bcrypt.checkpw(password.encode(), hash.encode())
