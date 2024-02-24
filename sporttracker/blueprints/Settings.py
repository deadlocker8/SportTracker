import logging
from gettext import gettext

from flask import Blueprint, render_template, redirect, url_for, abort, flash
from flask_bcrypt import Bcrypt
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel, field_validator, ConfigDict

from sporttracker.logic import Constants
from sporttracker.logic.Constants import MIN_PASSWORD_LENGTH
from sporttracker.logic.model.CustomTrackField import (
    get_custom_fields_by_track_type,
    CustomTrackField,
    CustomTrackFieldType,
    RESERVED_FIELD_NAMES,
)
from sporttracker.logic.model.Participant import Participant
from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.User import (
    User,
    Language,
    TrackInfoItem,
    TrackInfoItemType,
)
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class EditSelfUserFormModel(BaseModel):
    password: str


class EditSelfLanguageFormModel(BaseModel):
    language: str


class EditSelfTrackInfoItemsModel(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )


class CustomTrackFieldFormModel(BaseModel):
    name: str
    type: str
    track_type: str
    is_required: bool = False

    @field_validator(
        *[
            'is_required',
        ],
        mode='before',
    )
    def averageHeartRateCheck(cls, value: str, info) -> str | None:
        if isinstance(value, str):
            value = value.strip()
        if value == '':
            return None
        return value


class ParticipantFormModel(BaseModel):
    name: str


def construct_blueprint():
    settings = Blueprint('settings', __name__, static_folder='static', url_prefix='/settings')

    @settings.route('/settings')
    @login_required
    def settingsShow():
        infoItems: list[TrackInfoItem] = TrackInfoItem.query.filter(
            TrackInfoItem.user_id == current_user.id
        ).all()

        participants = Participant.query.filter(Participant.user_id == current_user.id).all()

        infoItems.sort(key=lambda item: item.type.get_localized_name().lower())

        return render_template(
            'settings/settings.jinja2',
            userLanguage=current_user.language.name,
            customFieldsByTrackType=get_custom_fields_by_track_type(),
            participants=participants,
            infoItems=infoItems,
        )

    @settings.route('/editSelfPost', methods=['POST'])
    @login_required
    @validate()
    def editSelfPost(form: EditSelfUserFormModel):
        user = User.query.filter(User.id == current_user.id).first()

        if user is None:
            abort(404)

        password = form.password.strip()

        if not password:
            return render_template(
                'settings/settings.jinja2',
                errorMessage='Password must not be empty',
                userLanguage=current_user.language.name,
                customFieldsByTrackType=get_custom_fields_by_track_type(),
            )

        if len(password) < MIN_PASSWORD_LENGTH:
            return render_template(
                'settings/settings.jinja2',
                errorMessage=f'Password must be at least {MIN_PASSWORD_LENGTH} characters long',
                userLanguage=current_user.language.name,
                customFieldsByTrackType=get_custom_fields_by_track_type(),
            )

        user.password = Bcrypt().generate_password_hash(password).decode('utf-8')

        LOGGER.debug(f'Updated own user: {user.username}')
        db.session.commit()

        return redirect(url_for('settings.settingsShow'))

    @settings.route('/editSelfLanguagePost', methods=['POST'])
    @login_required
    @validate()
    def editSelfLanguagePost(form: EditSelfLanguageFormModel):
        user = User.query.filter(User.id == current_user.id).first()

        if user is None:
            abort(404)

        user.language = Language(form.language)  # type: ignore[call-arg]

        LOGGER.debug(f'Updated language for user: {user.username} to {form.language}')
        db.session.commit()

        return redirect(url_for('settings.settingsShow'))

    @settings.route('/editSelfTrackInfoItems', methods=['POST'])
    @login_required
    @validate()
    def editSelfTrackInfoItems(form: EditSelfTrackInfoItemsModel):
        user = User.query.filter(User.id == current_user.id).first()

        if user is None:
            abort(404)

        for itemType in TrackInfoItemType:
            trackInfoItem = (
                TrackInfoItem.query.filter(TrackInfoItem.user_id == current_user.id)
                .filter(TrackInfoItem.type == itemType)
                .first()
            )

            if form.model_extra is None:
                abort(400)

            for itemName, itemValue in form.model_extra.items():
                if itemType.name == itemName:
                    trackInfoItem.is_activated = itemValue.strip().lower() == 'on'
                    break
            else:
                trackInfoItem.is_activated = False

        db.session.commit()

        LOGGER.debug(f'Updated track info items for user: {user.username}')

        return redirect(url_for('settings.settingsShow'))

    @settings.route('/customFields/add/<string:track_type>')
    @login_required
    def customFieldsAdd(track_type: str):
        trackType = TrackType(track_type)  # type: ignore[call-arg]
        return render_template('settings/customFieldsForm.jinja2', trackType=trackType)

    @settings.route('/customFields/post', methods=['POST'])
    @login_required
    @validate()
    def customFieldsAddPost(form: CustomTrackFieldFormModel):
        if not __is_allowed_custom_field_name(form):
            return redirect(url_for('settings.customFieldsAdd', track_type=form.track_type))

        track = CustomTrackField(
            name=form.name,
            type=CustomTrackFieldType(form.type),  # type: ignore[call-arg]
            track_type=TrackType(form.track_type),  # type: ignore[call-arg]
            is_required=form.is_required,
            user_id=current_user.id,
        )
        LOGGER.debug(f'Saved new custom field: {track}')
        db.session.add(track)
        db.session.commit()

        return redirect(url_for('settings.settingsShow'))

    @settings.route('/customFields/edit/<int:field_id>')
    @login_required
    def customFieldsEdit(field_id: int):
        field: CustomTrackField | None = (
            CustomTrackField.query.join(User)
            .filter(User.username == current_user.username)
            .filter(CustomTrackField.id == field_id)
            .first()
        )

        if field is None:
            abort(404)

        fieldModel = CustomTrackFieldFormModel(
            name=field.name,  # type: ignore[arg-type]
            type=field.type,
            track_type=field.track_type.name,
            is_required=field.is_required,
        )

        return render_template(
            'settings/customFieldsForm.jinja2', field=fieldModel, field_id=field_id
        )

    @settings.route('/customFields/edit/<int:field_id>', methods=['POST'])
    @login_required
    @validate()
    def customFieldsEditPost(field_id: int, form: CustomTrackFieldFormModel):
        field: CustomTrackField | None = (
            CustomTrackField.query.join(User)
            .filter(User.username == current_user.username)
            .filter(CustomTrackField.id == field_id)
            .first()
        )

        if field is None:
            abort(404)

        if field.name != form.name:
            if not __is_allowed_custom_field_name(form):
                return redirect(url_for('settings.customFieldsEdit', field_id=field_id))

        field.name = form.name  # type: ignore[assignment]
        field.type = form.type
        field.track_type = form.track_type
        field.is_required = form.is_required

        LOGGER.debug(f'Updated custom field: {field}')
        db.session.commit()

        return redirect(url_for('settings.settingsShow'))

    @settings.route('/customFields/delete/<int:field_id>')
    @login_required
    def customFieldsDelete(field_id: int):
        field: CustomTrackField | None = (
            CustomTrackField.query.join(User)
            .filter(User.username == current_user.username)
            .filter(CustomTrackField.id == field_id)
            .first()
        )

        if field is None:
            abort(404)

        LOGGER.debug(f'Deleted custom field: {field}')
        db.session.delete(field)
        db.session.commit()

        return redirect(url_for('settings.settingsShow'))

    @settings.route('/participants/add')
    @login_required
    def participantsAdd():
        return render_template('settings/participantsForm.jinja2')

    @settings.route('/participants/post', methods=['POST'])
    @login_required
    @validate()
    def participantsAddPost(form: ParticipantFormModel):
        participant = Participant(name=form.name, user_id=current_user.id)
        LOGGER.debug(f'Saved new participant: {participant}')
        db.session.add(participant)
        db.session.commit()

        return redirect(url_for('settings.settingsShow'))

    @settings.route('/participants/edit/<int:participant_id>')
    @login_required
    def participantsEdit(participant_id: int):
        participant: Participant | None = (
            Participant.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Participant.id == participant_id)
            .first()
        )

        if participant is None:
            abort(404)

        participantModel = ParticipantFormModel(name=participant.name)  # type: ignore[arg-type]

        return render_template(
            'settings/participantsForm.jinja2', participant=participantModel, participant_id=participant_id
        )

    @settings.route('/participants/edit/<int:participant_id>', methods=['POST'])
    @login_required
    @validate()
    def participantsEditPost(participant_id: int, form: ParticipantFormModel):
        participant: Participant | None = (
            Participant.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Participant.id == participant_id)
            .first()
        )

        if participant is None:
            abort(404)

        if participant.name != form.name:
            if not __is_allowed_participant_name(form):
                return redirect(url_for('settings.participantsForm', participant_id=participant_id))

        participant.name = form.name  # type: ignore[assignment]

        LOGGER.debug(f'Updated participant: {participant}')
        db.session.commit()

        return redirect(url_for('settings.settingsShow'))

    @settings.route('/participants/delete/<int:participant_id>')
    @login_required
    def participantsDelete(participant_id: int):
        participant: Participant | None = (
            Participant.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Participant.id == participant_id)
            .first()
        )

        if participant is None:
            abort(404)

        LOGGER.debug(f'Deleted participant: {participant}')
        db.session.delete(participant)
        db.session.commit()

        return redirect(url_for('settings.settingsShow'))

    def __is_allowed_custom_field_name(form: CustomTrackFieldFormModel):
        if form.name.lower() in RESERVED_FIELD_NAMES:
            flash(
                gettext(
                    'The specified field name "{0}" conflicts with a reserved field name and therefore can\'t '
                    'be used as custom field name.'
                ).format(form.name)
            )
            return False

        existingCustomFields = (
            CustomTrackField.query.filter(CustomTrackField.user_id == current_user.id)
            .filter(CustomTrackField.track_type == form.track_type)
            .all()
        )
        existingCustomFieldNames = [item.name.lower() for item in existingCustomFields]
        if form.name.lower() in existingCustomFieldNames:
            flash(gettext('The specified field name "{0}" already exists.').format(form.name))
            return False

        return True

    def __is_allowed_participant_name(form: ParticipantFormModel):
        existingParticipants = Participant.query.filter(Participant.user_id == current_user.id).all()
        existingParticipantNames = [item.name.lower() for item in existingParticipants]
        if form.name.lower() in existingParticipantNames:
            flash(gettext('The specified participant name "{0}" already exists.').format(form.name))
            return False

        return True

    return settings
