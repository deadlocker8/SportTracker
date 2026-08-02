from sporttracker.db import db
from sporttracker.user.CustomWorkoutFieldEntity import CustomWorkoutField, CustomWorkoutFieldType
from sporttracker.user.ParticipantEntity import Participant
from sporttracker.workout.WorkoutType import WorkoutType


class TestParticipants:
    URL = '/api/v2/settings/participants'

    def test_list_empty(self, client):
        response = client.get(self.URL)
        assert response.status_code == 200
        assert response.get_json() == []

    def test_list_with_entries(self, client, app, user):
        with app.app_context():
            participant = Participant(name='John Doe', user_id=user.id)
            db.session.add(participant)
            db.session.commit()
            participantId = participant.id

        response = client.get(self.URL)
        assert response.status_code == 200
        assert response.get_json() == [{'id': participantId, 'name': 'John Doe'}]


class TestCustomFields:
    URL = '/api/v2/settings/customFields'

    def test_list_empty(self, client):
        response = client.get(self.URL)
        assert response.status_code == 200
        assert response.get_json() == {'BIKING': [], 'RUNNING': [], 'HIKING': [], 'FITNESS': []}

    def test_list_with_entries(self, client, app, user):
        with app.app_context():
            customWorkoutField = CustomWorkoutField(
                type=CustomWorkoutFieldType.STRING,
                workout_type=WorkoutType.BIKING,
                name='bike',
                is_required=True,
                user_id=user.id,
            )
            db.session.add(customWorkoutField)
            db.session.commit()
            fieldId = customWorkoutField.id

        response = client.get(self.URL)
        assert response.status_code == 200
        jsonData = response.get_json()
        assert jsonData['BIKING'] == [
            {'id': fieldId, 'workout_type': 'BIKING', 'field_type': 'STRING', 'name': 'bike', 'is_required': True}
        ]
        assert jsonData['RUNNING'] == []
        assert jsonData['HIKING'] == []
        assert jsonData['FITNESS'] == []
