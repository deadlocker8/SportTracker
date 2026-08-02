from sporttracker.db import db
from sporttracker.workout.fitness.FitnessWorkoutEntity import FitnessWorkout
from sporttracker.workout.heartRate.HeartRateEntity import HeartRateEntity


class TestFitnessWorkout:
    URL = '/api/v2/workouts/fitnessWorkout'

    @staticmethod
    def __build_payload(**overrides):
        payload = {
            'name': 'My Fitness Workout',
            'workout_type': 'FITNESS',
            'date': '2026-01-15',
            'start_time': '15:30',
            'duration': 1800,
            'average_heart_rate': 130,
            'fitness_workout_type': 'DURATION_BASED',
            'fitness_workout_categories': ['ARMS', 'CORE'],
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
        jsonData = response.get_json()
        assert len(jsonData) == 1
        assert jsonData[0]['id'] == 1
        assert jsonData[0]['workout_type'] == 'FITNESS'
        assert jsonData[0]['name'] == 'My Fitness Workout'
        assert jsonData[0]['date'] == '2026-01-15'
        assert jsonData[0]['start_time'] == '15:30'
        assert jsonData[0]['duration'] == 1800
        assert jsonData[0]['average_heart_rate'] == 130
        assert jsonData[0]['participants'] == []
        assert jsonData[0]['fitness_workout_type'] == 'DURATION_BASED'
        assert set(jsonData[0]['fitness_workout_categories']) == {'ARMS', 'CORE'}
        assert jsonData[0]['custom_fields'] == {}

    def test_add_invalid_workout_type(self, client):
        response = client.post(self.URL, json=self.__build_payload(workout_type='INVALID'))
        assert response.status_code == 400

    def test_add_non_fitness_workout_type(self, client):
        response = client.post(self.URL, json=self.__build_payload(workout_type='BIKING'))
        assert response.status_code == 400

    def test_add_invalid_fitness_workout_type(self, client):
        response = client.post(self.URL, json=self.__build_payload(fitness_workout_type='INVALID'))
        assert response.status_code == 400

    def test_add_invalid_fitness_workout_category(self, client):
        response = client.post(self.URL, json=self.__build_payload(fitness_workout_categories=['INVALID']))
        assert response.status_code == 400

    def test_add_invalid_json(self, client):
        response = client.post(self.URL, json={'name': 'My Fitness Workout'})
        assert response.status_code == 400

    def test_add_heart_rate_data_success(self, client, app):
        workoutId = self.__add_workout(client)

        response = client.post(
            f'/api/v2/workouts/fitnessWorkout/{workoutId}/addHeartRateData',
            json={
                'data': [
                    {'timestamp': '2026-01-15 15:30:00', 'bpm': 120},
                    {'timestamp': '2026-01-15 15:30:01', 'bpm': 140},
                ]
            },
        )
        assert response.status_code == 200

        with app.app_context():
            workout = db.session.get(FitnessWorkout, workoutId)
            assert workout.average_heart_rate == 130  # type: ignore[union-attr]

            heartRateData = HeartRateEntity.query.filter(HeartRateEntity.workout_id == workoutId).all()
            assert len(heartRateData) == 2

    def test_add_heart_rate_data_nonexistent_workout(self, client):
        response = client.post('/api/v2/workouts/fitnessWorkout/999/addHeartRateData', json={'data': []})
        assert response.status_code == 404

    def test_add_heart_rate_data_invalid_json(self, client):
        workoutId = self.__add_workout(client)

        response = client.post(
            f'/api/v2/workouts/fitnessWorkout/{workoutId}/addHeartRateData',
            json={'data': [{'timestamp': '2026-01-15 15:30:00'}]},
        )
        assert response.status_code == 400
