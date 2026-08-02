from sporttracker.bodyWeight.BodyWeightEntity import BodyWeight
from sporttracker.user.UserEntity import User
from tests.TestConstants import TEST_USERNAME


class TestBodyWeight:
    URL = '/api/v2/bodyWeight'

    def test_add_valid(self, client, app):
        response = client.post(
            self.URL,
            json={
                'data': [
                    {'timestamp': '2026-01-15 15:30:00', 'weight': 80500},
                    {'timestamp': '2026-01-16 15:30:00', 'weight': 80300},
                ]
            },
        )
        assert response.status_code == 200

        with app.app_context():
            user = User.query.filter(User.username == TEST_USERNAME).first()
            entries = BodyWeight.query.filter(BodyWeight.user_id == user.id).all()
            assert len(entries) == 2
            assert entries[0].weight == 80500
            assert entries[1].weight == 80300

    def test_add_invalid_json(self, client):
        response = client.post(self.URL, json={'data': [{'timestamp': '2026-01-15 15:30:00'}]})
        assert response.status_code == 400
