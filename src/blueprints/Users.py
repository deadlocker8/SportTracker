from dataclasses import dataclass

from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils.auth.SessionLoginWrapper import require_login
from flask import Blueprint, render_template, redirect, url_for, abort
from flask_pydantic import validate
from pydantic import BaseModel

from logic import Constants
from logic.model.Models import db, User

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class NewUserFormModel(BaseModel):
    username: str
    password: str


class EditUserFormModel(BaseModel):
    old_username: str
    username: str
    password: str


@dataclass
class UserModel:
    username: str


MIN_PASSWORD_LENGTH = 3


def construct_blueprint():
    users = Blueprint('users', __name__, static_folder='static', url_prefix='/users')

    @users.route('/')
    @require_login
    def listUsers():
        allUsers = User.query.order_by(User.username.asc()).all()

        return render_template('users.jinja2', users=allUsers)

    @users.route('/add')
    @require_login
    def add():
        return render_template('userForm.jinja2')

    @users.route('/post', methods=['POST'])
    @require_login
    @validate()
    def addPost(form: NewUserFormModel):
        username = form.username.strip().lower()
        password = form.password.strip()

        if __user_already_exists(username):
            return render_template('userForm.jinja2', errorMessage=f'Username "{form.username}" already exists')

        if not password:
            return render_template('userForm.jinja2', errorMessage=f'Password must not be empty')

        if len(password) < MIN_PASSWORD_LENGTH:
            return render_template('userForm.jinja2',
                                   errorMessage=f'Password must be at least {MIN_PASSWORD_LENGTH} characters long')

        user = User(username=form.username, password=form.password)
        LOGGER.debug(f'Saved new user: {user.username}')
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('users.listUsers'))

    @users.route('/edit/<int:user_id>')
    @require_login
    def edit(user_id: int):
        user = User.query.filter(User.id == user_id).first()

        if user is None:
            abort(404)

        userModel = UserModel(username=user.username)

        return render_template('userForm.jinja2', user=userModel, user_id=user_id)

    @users.route('/edit/<int:user_id>', methods=['POST'])
    @require_login
    @validate()
    def editPost(user_id: int, form: EditUserFormModel):
        user = User.query.filter(User.id == user_id).first()

        if user is None:
            abort(404)

        old_username = form.old_username.strip().lower()
        username = form.username.strip().lower()
        password = form.password.strip()

        if username != old_username:
            if __user_already_exists(username):
                return render_template('userForm.jinja2', user=user, user_id=user_id, errorMessage=f'Username "{form.username}" already exists')

        if not password:
            return render_template('userForm.jinja2', user=user, user_id=user_id, errorMessage=f'Password must not be empty')

        if len(password) < MIN_PASSWORD_LENGTH:
            return render_template('userForm.jinja2', user=user, user_id=user_id, errorMessage=f'Password must be at least {MIN_PASSWORD_LENGTH} characters long')

        user.username = form.username
        user.password = form.password

        LOGGER.debug(f'Updated user: {user.username}')
        db.session.commit()

        return redirect(url_for('users.listUsers'))

    @users.route('/delete/<int:user_id>')
    @require_login
    def delete(user_id: int):
        user = User.query.filter(User.id == user_id).first()

        if user is None:
            abort(404)

        LOGGER.debug(f'Deleted user: {user.username}')
        db.session.delete(user)
        db.session.commit()

        return redirect(url_for('users.listUsers'))

    def __user_already_exists(username: str) -> bool:
        return User.query.filter(User.username == username).first() is not None

    return users
