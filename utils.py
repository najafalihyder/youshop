import bcrypt


def hash_passowrd(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hash):
    return bcrypt.checkpw(password.encode(), hash.encode())

def login_required():
    def check_session(request):
        if not request.session['user_id']:
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={}
            )
    return check_session