from sporttracker.db import db
from sporttracker.maintenance.MaintenanceEntity import Maintenance
from sporttracker.workout.WorkoutType import WorkoutType


class TestMaintenances:
    URL = '/api/v2/maintenances'

    def test_list_empty(self, client):
        response = client.get(self.URL)
        assert response.status_code == 200
        assert response.get_json() == []

    def test_list_with_entries(self, client, app, user):
        with app.app_context():
            maintenance = Maintenance(
                type=WorkoutType.BIKING,
                description='Chain cleaning',
                user_id=user.id,
                is_reminder_active=True,
                reminder_limit=1000,
                custom_workout_field_id=None,
                custom_workout_field_value=None,
            )
            db.session.add(maintenance)
            db.session.commit()
            maintenanceId = maintenance.id

        response = client.get(self.URL)
        assert response.status_code == 200
        assert response.get_json() == [
            {
                'id': maintenanceId,
                'workout_type': 'BIKING',
                'description': 'Chain cleaning',
                'is_reminder_active': True,
                'reminder_limit': 1000,
                'is_reminder_triggered': False,
                'limit_exceeded_distance': None,
            }
        ]
