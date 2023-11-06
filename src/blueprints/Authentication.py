from flask import Blueprint, render_template, redirect, url_for, request, session
from flask_login import login_user, logout_user, login_required, current_user

from logic.model.Models import User


def construct_blueprint():
    authentication = Blueprint('authentication', __name__)

    @authentication.route('/login')
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('general.index'))

        return render_template('login.jinja2')

    @authentication.route('/login', methods=['POST'])
    def login_post():
        username = request.form.get('username').strip().lower()
        password = request.form.get('password').strip()

        if username is None:
            return render_template('login.jinja2', message='Unbekannter Nutzer')

        user = User.query.filter_by(username=username).first()

        if user is None:
            return render_template('login.jinja2', message='Unbekannter Nutzer')

        if password is None:
            return render_template('login.jinja2', message='Error parameter "password"!')

        if password != user.password:
            return render_template('login.jinja2', message='Falsches Passwort')

        user = User.query.filter_by(username=username).first()
        if user is None:
            return render_template('login.jinja2', message='Unbekannter Nutzer')

        login_user(user, remember=True)
        return redirect(url_for('general.index'))

    @authentication.route('/logout')
    @login_required
    def logout():
        logout_user()

        return redirect(url_for('authentication.login'))

    return authentication
