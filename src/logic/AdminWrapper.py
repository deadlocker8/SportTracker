from functools import wraps

from flask import redirect, url_for
from flask_login import current_user


def admin_role_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.isAdmin:
            return redirect(url_for('authentication.login'))

        # redirect to requested url
        return func(*args, **kwargs)

    return decorated_view
