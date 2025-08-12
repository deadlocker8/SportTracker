import logging

from flask import Blueprint, render_template, abort, redirect, url_for
from flask_login import login_required

from sporttracker.logic import Constants
from sporttracker.logic.model.db import db
from sporttracker.logic.service.NotificationService import NotificationService

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    notifications = Blueprint('notifications', __name__, static_folder='static', url_prefix='/notifications')

    @notifications.route('/')
    @login_required
    def listNotifications():
        return render_template(
            'notifications/notifications.jinja2',
            notifications=NotificationService.get_all_notifications(),
        )

    @notifications.route('/delete/<int:notification_id>')
    @login_required
    def delete(notification_id: int):
        notification = NotificationService.get_notification_by_id(notification_id)

        if notification is None:
            abort(404)

        LOGGER.debug(f'Deleted notification: {notification_id}')
        db.session.delete(notification)
        db.session.commit()

        return redirect(url_for('notifications.listNotifications'))

    return notifications
