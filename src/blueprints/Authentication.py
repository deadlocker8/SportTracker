from flask import Blueprint, render_template, redirect, url_for, request, session

from logic.UserService import UserService


def construct_blueprint(userService: UserService):
    USERNAME = 'r'

    authentication = Blueprint('authentication', __name__)

    @authentication.route('/login')
    def login():
        return render_template('login.jinja2')

    @authentication.route('/login', methods=['POST'])
    def login_post():
        password = request.form.get('password')

        expectedPassword = userService.get_password_by_username(USERNAME)
        if password is None:
            return render_template('login.jinja2', message='Error parameter "password"!')

        if password != expectedPassword:
            return render_template('login.jinja2', message='Falsches Passwort')

        session['authorized'] = True
        return redirect(url_for('general.index'))

    @authentication.route('/logout')
    def logout():
        del session['authorized']
        return redirect(url_for('authentication.login'))

    return authentication
