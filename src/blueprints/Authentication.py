from flask import Blueprint, render_template, redirect, url_for, request, session

from logic.model.Models import User


def construct_blueprint():
    authentication = Blueprint('authentication', __name__)

    @authentication.route('/login')
    def login():
        if 'authorized' in session:
            return redirect(url_for('tracks.listTracks'))

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

        session['authorized'] = True
        session['username'] = username
        user = User.query.filter_by(username=username).first()
        if user is None:
            return render_template('login.jinja2', message='Unbekannter Nutzer')
        session['userId'] = user.id

        return redirect(url_for('tracks.listTracks'))

    @authentication.route('/logout')
    def logout():
        del session['authorized']
        del session['username']
        del session['userId']
        return redirect(url_for('authentication.login'))

    return authentication
