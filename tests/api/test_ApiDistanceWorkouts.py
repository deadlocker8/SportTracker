import io
from datetime import datetime

from sporttracker.db import db
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.plannedTour.TravelDirection import TravelDirection
from sporttracker.plannedTour.TravelType import TravelType
from sporttracker.user.ParticipantEntity import Participant
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.heartRate.HeartRateEntity import HeartRateEntity

GPX_CONTENT = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">\n'
    '  <trk>\n'
    '    <name>Test Track</name>\n'
    '    <trkseg>\n'
    '      <trkpt lat="51.3390" lon="12.3710"><ele>100</ele></trkpt>\n'
    '      <trkpt lat="51.3395" lon="12.3720"><ele>110</ele></trkpt>\n'
    '    </trkseg>\n'
    '  </trk>\n'
    '</gpx>\n'
).encode('utf-8')


class TestDistanceWorkout:
    URL = '/api/v2/workouts/distanceWorkout'

    @staticmethod
    def __build_payload(**overrides):
        payload = {
            'name': 'My Workout',
            'workout_type': 'BIKING',
            'date': '2026-01-15',
            'start_time': '15:30',
            'distance': 22500,
            'duration': 3600,
            'average_heart_rate': 130,
            'elevation_sum': 650,
            'participants': [],
        }
        payload.update(overrides)
        return payload

    def __add_workout(self, client) -> int:
        response = client.post(self.URL, json=self.__build_payload())
        assert response.status_code == 200
        return response.get_json()['id']

    def test_list_empty(self, client):
        response = client.get(self.URL)
        assert response.status_code == 200
        assert response.get_json() == []

    def test_add_valid(self, client):
        response = client.post(self.URL, json=self.__build_payload())
        assert response.status_code == 200
        assert response.get_json() == {'id': 1}

    def test_list_after_add(self, client):
        client.post(self.URL, json=self.__build_payload())

        response = client.get(self.URL)
        assert response.status_code == 200
        assert response.get_json() == [
            {
                'id': 1,
                'workout_type': 'BIKING',
                'name': 'My Workout',
                'date': '2026-01-15',
                'start_time': '15:30',
                'duration': 3600,
                'average_heart_rate': 130,
                'participants': [],
                'distance': 22500,
                'elevation_sum': 650,
                'planned_tour_id': None,
                'has_gpx': False,
                'custom_fields': {},
            }
        ]

    def test_add_invalid_workout_type(self, client):
        response = client.post(self.URL, json=self.__build_payload(workout_type='INVALID'))
        assert response.status_code == 400

    def test_add_non_distance_workout_type(self, client):
        response = client.post(self.URL, json=self.__build_payload(workout_type='FITNESS'))
        assert response.status_code == 400

    def test_add_invalid_json(self, client):
        response = client.post(self.URL, json={'name': 'My Workout'})
        assert response.status_code == 400

    def test_add_with_participant(self, client, app, user):
        with app.app_context():
            participant = Participant(name='John Doe', user_id=user.id)
            db.session.add(participant)
            db.session.commit()
            participantId = participant.id

        response = client.post(self.URL, json=self.__build_payload(participants=[participantId]))
        assert response.status_code == 200

        jsonData = client.get(self.URL).get_json()
        assert jsonData[0]['participants'] == [participantId]

    def test_add_with_planned_tour(self, client, app, user):
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
            plannedTourId = plannedTour.id

        response = client.post(self.URL, json=self.__build_payload(planned_tour_id=plannedTourId))
        assert response.status_code == 200

        jsonData = client.get(self.URL).get_json()
        assert jsonData[0]['planned_tour_id'] == plannedTourId

    def test_add_with_nonexistent_planned_tour(self, client):
        response = client.post(self.URL, json=self.__build_payload(planned_tour_id=999))
        assert response.status_code == 400

    def test_add_with_custom_fields(self, client):
        response = client.post(self.URL, json=self.__build_payload(custom_fields={'bike': 'Cube'}))
        assert response.status_code == 200

        jsonData = client.get(self.URL).get_json()
        assert jsonData[0]['custom_fields'] == {'bike': 'Cube'}

    def test_add_gpx_track_success(self, client):
        workoutId = self.__add_workout(client)

        response = client.post(
            f'/api/v2/workouts/distanceWorkout/{workoutId}/addGpxTrack',
            data={'gpxTrack': (io.BytesIO(GPX_CONTENT), 'test.gpx')},
            content_type='multipart/form-data',
        )
        assert response.status_code == 200

        jsonData = client.get(self.URL).get_json()
        assert jsonData[0]['has_gpx'] is True

    def test_add_gpx_track_nonexistent_workout(self, client):
        response = client.post(
            '/api/v2/workouts/distanceWorkout/999/addGpxTrack',
            data={'gpxTrack': (io.BytesIO(GPX_CONTENT), 'test.gpx')},
            content_type='multipart/form-data',
        )
        assert response.status_code == 404

    def test_add_gpx_track_no_file(self, client):
        workoutId = self.__add_workout(client)

        response = client.post(f'/api/v2/workouts/distanceWorkout/{workoutId}/addGpxTrack')
        assert response.status_code == 400

    def test_add_heart_rate_data_success(self, client, app):
        workoutId = self.__add_workout(client)

        response = client.post(
            f'/api/v2/workouts/distanceWorkout/{workoutId}/addHeartRateData',
            json={
                'data': [
                    {'timestamp': '2026-01-15 15:30:00', 'bpm': 120},
                    {'timestamp': '2026-01-15 15:30:01', 'bpm': 140},
                ]
            },
        )
        assert response.status_code == 200

        with app.app_context():
            workout = db.session.get(DistanceWorkout, workoutId)
            assert workout.average_heart_rate == 130  # type: ignore[union-attr]

            heartRateData = HeartRateEntity.query.filter(HeartRateEntity.workout_id == workoutId).all()
            assert len(heartRateData) == 2

    def test_add_heart_rate_data_nonexistent_workout(self, client):
        response = client.post('/api/v2/workouts/distanceWorkout/999/addHeartRateData', json={'data': []})
        assert response.status_code == 404

    def test_add_heart_rate_data_invalid_json(self, client):
        workoutId = self.__add_workout(client)

        response = client.post(
            f'/api/v2/workouts/distanceWorkout/{workoutId}/addHeartRateData',
            json={'data': [{'timestamp': '2026-01-15 15:30:00'}]},
        )
        assert response.status_code == 400
