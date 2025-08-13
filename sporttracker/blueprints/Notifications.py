import logging

from flask import Blueprint, render_template, abort, redirect, url_for, request
from flask_login import login_required

from sporttracker.logic import Constants
from sporttracker.logic.model.db import db
from sporttracker.logic.service.NotificationService import NotificationService

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(notification_service: NotificationService):
    notifications = Blueprint('notifications', __name__, static_folder='static', url_prefix='/notifications')

    @notifications.route('/')
    @login_required
    def listNotifications():
        page_number = request.args.get('pageNumber')

        try:
            page_number_value = int(page_number)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            page_number_value = 1

        if page_number_value < 1:
            page_number_value = 1

        return render_template(
            'notifications/notifications.jinja2',
            pagination=notification_service.get_notifications_paginated(page_number_value),
        )

    @notifications.route('/delete/<int:notification_id>')
    @login_required
    def delete(notification_id: int):
        notification = notification_service.get_notification_by_id(notification_id)

        if notification is None:
            abort(404)

        LOGGER.debug(f'Deleted notification: {notification_id}')
        db.session.delete(notification)
        db.session.commit()

        return redirect(url_for('notifications.listNotifications'))

    return notifications
