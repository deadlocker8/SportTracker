from sporttracker.monthGoal.MonthGoalEntity import MonthGoalDistance
from sporttracker.workout.WorkoutType import WorkoutType


class TestMonthGoalDistance:
    URL = '/api/v2/monthGoals/monthGoalDistance'

    @staticmethod
    def __build_payload(workout_type='BIKING'):
        return {
            'workout_type': workout_type,
            'year': 2026,
            'month': 1,
            'distance_minimum': 100.0,
            'distance_perfect': 200.0,
        }

    def test_list_empty(self, client):
        response = client.get(self.URL)
        assert response.status_code == 200
        assert response.get_json() == []

    def test_add_valid(self, client):
        response = client.post(self.URL, json=self.__build_payload())
        assert response.status_code == 200
        assert response.get_json() == {'id': 1}

    def test_add_valid_saves_month_goal(self, client, app):
        client.post(self.URL, json=self.__build_payload())

        with app.app_context():
            monthGoals = MonthGoalDistance.query.all()
            assert len(monthGoals) == 1
            assert monthGoals[0].type == WorkoutType.BIKING
            assert monthGoals[0].year == 2026
            assert monthGoals[0].month == 1
            assert monthGoals[0].distance_minimum == 100
            assert monthGoals[0].distance_perfect == 200

    def test_list_after_add(self, client):
        client.post(self.URL, json=self.__build_payload())

        response = client.get(self.URL)
        assert response.status_code == 200
        assert response.get_json() == [
            {
                'id': 1,
                'workout_type': 'BIKING',
                'year': 2026,
                'month': 1,
                'distance_minimum': 100,
                'distance_perfect': 200,
            }
        ]

    def test_add_invalid_workout_type(self, client):
        response = client.post(self.URL, json=self.__build_payload(workout_type='INVALID'))
        assert response.status_code == 400

    def test_add_fitness_workout_type_not_allowed(self, client):
        response = client.post(self.URL, json=self.__build_payload(workout_type='FITNESS'))
        assert response.status_code == 400

    def test_add_invalid_json(self, client):
        response = client.post(self.URL, json={'workout_type': 'BIKING'})
        assert response.status_code == 400


class TestMonthGoalCount:
    URL = '/api/v2/monthGoals/monthGoalCount'

    @staticmethod
    def __build_payload(workout_type='BIKING'):
        return {
            'workout_type': workout_type,
            'year': 2026,
            'month': 1,
            'count_minimum': 3.0,
            'count_perfect': 5.0,
        }

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
                'year': 2026,
                'month': 1,
                'count_minimum': 3,
                'count_perfect': 5,
            }
        ]

    def test_add_fitness_workout_type_allowed(self, client):
        response = client.post(self.URL, json=self.__build_payload(workout_type='FITNESS'))
        assert response.status_code == 200

    def test_add_invalid_workout_type(self, client):
        response = client.post(self.URL, json=self.__build_payload(workout_type='INVALID'))
        assert response.status_code == 400

    def test_add_invalid_json(self, client):
        response = client.post(self.URL, json={'workout_type': 'BIKING'})
        assert response.status_code == 400


class TestMonthGoalDuration:
    URL = '/api/v2/monthGoals/monthGoalDuration'

    @staticmethod
    def __build_payload(workout_type='BIKING'):
        return {
            'workout_type': workout_type,
            'year': 2026,
            'month': 1,
            'duration_minimum': 60.0,
            'duration_perfect': 180.0,
        }

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
                'year': 2026,
                'month': 1,
                'duration_minimum': 60,
                'duration_perfect': 180,
            }
        ]

    def test_add_fitness_workout_type_allowed(self, client):
        response = client.post(self.URL, json=self.__build_payload(workout_type='FITNESS'))
        assert response.status_code == 200

    def test_add_invalid_workout_type(self, client):
        response = client.post(self.URL, json=self.__build_payload(workout_type='INVALID'))
        assert response.status_code == 400

    def test_add_invalid_json(self, client):
        response = client.post(self.URL, json={'workout_type': 'BIKING'})
        assert response.status_code == 400
