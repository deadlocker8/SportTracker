import logging
from dataclasses import dataclass
from gettext import gettext

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_bcrypt import Bcrypt
from flask_login import fresh_login_required
from flask_pydantic import validate
from pydantic import BaseModel
from sqlalchemy import asc, func

from sporttracker import Constants
from sporttracker.authentication.AdminWrapper import admin_role_required
from sporttracker.Constants import MIN_PASSWORD_LENGTH
from sporttracker.user.UserEntity import (
    User,
    Language,
    create_user,
)
from sporttracker.db import db
from sporttracker.maintenance.MaintenanceFilterStateEntity import get_maintenance_filter_state_by_user
from sporttracker.plannedTour.PlannedTourFilterStateEntity import get_planned_tour_filter_state_by_user
from sporttracker.quickFilter.QuickFilterStateEntity import get_quick_filter_state_by_user
from sporttracker.tileHunting.TileHuntingFilterStateEntity import get_tile_hunting_filter_state_by_user

LOGGER = logging.getLogger(Constants.APP_NAME)


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
    isAdmin: bool


def construct_blueprint():
    users = Blueprint('users', __name__, static_folder='static', url_prefix='/users')

    @users.route('/')
    @admin_role_required
    @fresh_login_required
    def listUsers():
        allUsers = User.query.order_by(asc(func.lower(User.username))).all()

        return render_template('user/users.jinja2', users=allUsers)

    @users.route('/add')
    @admin_role_required
    @fresh_login_required
    def add():
        return render_template('user/userForm.jinja2')

    @users.route('/post', methods=['POST'])
    @admin_role_required
    @fresh_login_required
    @validate()
    def addPost(form: NewUserFormModel):
        username = form.username.strip().lower()
        password = form.password.strip()

        if __user_already_exists(username):
            return render_template(
                'user/userForm.jinja2',
                errorMessage=gettext('Username "{0}" already exists').format(form.username),
            )

        if not password:
            return render_template('user/userForm.jinja2', errorMessage=gettext('Password must not be empty'))

        if len(password) < MIN_PASSWORD_LENGTH:
            return render_template(
                'user/userForm.jinja2',
                errorMessage=gettext('Password must be at least {0} characters long').format(MIN_PASSWORD_LENGTH),
            )

        create_user(username=username, password=password, isAdmin=False, language=Language.ENGLISH)
        LOGGER.debug(f'Saved new user: {username}')

        return redirect(url_for('users.listUsers'))

    @users.route('/edit/<int:user_id>')
    @admin_role_required
    @fresh_login_required
    def edit(user_id: int):
        user = User.query.filter(User.id == user_id).first()

        if user is None:
            abort(404)

        userModel = UserModel(username=user.username, isAdmin=user.isAdmin)

        return render_template('user/userForm.jinja2', user=userModel, user_id=user_id)

    @users.route('/edit/<int:user_id>', methods=['POST'])
    @admin_role_required
    @fresh_login_required
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
                return render_template(
                    'user/userForm.jinja2',
                    user=user,
                    user_id=user_id,
                    errorMessage=gettext('Username "{0}" already exists').format(form.username),
                )

        if not password:
            return render_template(
                'user/userForm.jinja2',
                user=user,
                user_id=user_id,
                errorMessage=gettext('Password must not be empty'),
            )

        if len(password) < MIN_PASSWORD_LENGTH:
            return render_template(
                'user/userForm.jinja2',
                user=user,
                user_id=user_id,
                errorMessage=gettext('Password must be at least {0} characters long').format(MIN_PASSWORD_LENGTH),
            )

        user.username = username
        user.password = Bcrypt().generate_password_hash(password).decode('utf-8')

        LOGGER.debug(f'Updated user: {user.username}')
        db.session.commit()

        return redirect(url_for('users.listUsers'))

    @users.route('/delete/<int:user_id>')
    @admin_role_required
    @fresh_login_required
    def delete(user_id: int):
        user = User.query.filter(User.id == user_id).first()

        if user is None:
            abort(404)

        if user.isAdmin:
            abort(400)

        maintenanceFilterState = get_maintenance_filter_state_by_user(user.id)
        db.session.delete(maintenanceFilterState)
        db.session.commit()

        plannedTourFilterState = get_planned_tour_filter_state_by_user(user.id)
        db.session.delete(plannedTourFilterState)
        db.session.commit()

        quickFilterState = get_quick_filter_state_by_user(user.id)
        db.session.delete(quickFilterState)
        db.session.commit()

        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(user.id)
        db.session.delete(tileHuntingFilterState)
        db.session.commit()

        LOGGER.debug(f'Deleted user: {user.username}')
        db.session.delete(user)
        db.session.commit()

        return redirect(url_for('users.listUsers'))

    def __user_already_exists(username: str) -> bool:
        return User.query.filter(User.username == username).first() is not None

    return users
