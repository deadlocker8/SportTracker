from datetime import datetime

from sporttracker.db import db
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.plannedTour.TravelDirection import TravelDirection
from sporttracker.plannedTour.TravelType import TravelType
from sporttracker.workout.WorkoutType import WorkoutType


class TestPlannedTours:
    URL = '/api/v2/plannedTours'

    def test_list_empty(self, client):
        response = client.get(self.URL)
        assert response.status_code == 200
        assert response.get_json() == []

    def test_list_with_entries(self, client, app, user):
        with app.app_context():
            plannedTour = PlannedTour(
                type=WorkoutType.BIKING,
                name='Megatour',
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user.id,
                gpx_metadata_id=None,
                user_id=user.id,
                shared_users=[],
                arrival_method=TravelType.TRAIN,
                departure_method=TravelType.NONE,
                direction=TravelDirection.SINGLE,
                share_code=None,
            )
            db.session.add(plannedTour)
            db.session.commit()

        response = client.get(self.URL)
        assert response.status_code == 200
        jsonData = response.get_json()
        assert len(jsonData) == 1
        assert jsonData[0]['workout_type'] == 'BIKING'
        assert jsonData[0]['name'] == 'Megatour'
