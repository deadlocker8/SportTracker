from flask import Blueprint, render_template, redirect, url_for, request
from flask_babel import gettext
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required, current_user

from sporttracker.helpers.Helpers import is_allowed_redirect_url
from sporttracker.logic.model.User import User


def construct_blueprint():
    authentication = Blueprint('authentication', __name__)

    @authentication.route('/login')
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('general.index'))

        return render_template('login.jinja2')

    @authentication.route('/login', methods=['POST'])
    def login_post():
        username = request.form.get('username')
        password = request.form.get('password')

        if username is None:
            return render_template('login.jinja2', message=gettext('Unknown user'))

        username = username.strip().lower()

        user = User.query.filter_by(username=username).first()

        if user is None:
            return render_template('login.jinja2', message=gettext('Unknown user'))

        if password is None:
            return render_template('login.jinja2', message=gettext('Password must not be empty'))

        password = password.strip()

        if not Bcrypt().check_password_hash(user.password, password):
            return render_template('login.jinja2', message=gettext('Incorrect password'))

        login_user(user, remember=True)

        nextUrl = request.form.get('next', None)
        if is_allowed_redirect_url(nextUrl, request.host):
            return redirect(nextUrl or url_for('general.index'))

        return redirect(url_for('general.index'))

    @authentication.route('/logout')
    @login_required
    def logout():
        logout_user()

        return redirect(url_for('authentication.login'))

    return authentication
