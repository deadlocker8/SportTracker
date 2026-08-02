from sporttracker.api.Api import API_VERSION
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


class TestLogin:
    def test_login_success(self, app):
        response = app.test_client().post('/api/v2/login', data={'username': TEST_USERNAME, 'password': TEST_PASSWORD})
        assert response.status_code == 200

    def test_login_username_case_insensitive(self, app):
        response = app.test_client().post(
            '/api/v2/login', data={'username': TEST_USERNAME.upper(), 'password': TEST_PASSWORD}
        )
        assert response.status_code == 200

    def test_login_missing_username(self, app):
        response = app.test_client().post('/api/v2/login', data={'password': TEST_PASSWORD})
        assert response.status_code == 400

    def test_login_missing_password(self, app):
        response = app.test_client().post('/api/v2/login', data={'username': TEST_USERNAME})
        assert response.status_code == 400

    def test_login_unknown_user(self, app):
        response = app.test_client().post('/api/v2/login', data={'username': 'unknown_user', 'password': TEST_PASSWORD})
        assert response.status_code == 401

    def test_login_wrong_password(self, app):
        response = app.test_client().post(
            '/api/v2/login', data={'username': TEST_USERNAME, 'password': 'wrong_password'}
        )
        assert response.status_code == 401


class TestVersion:
    def test_version_logged_in(self, client):
        response = client.get('/api/v2/version')
        assert response.status_code == 200
        assert response.get_json() == {'version': API_VERSION}

    def test_version_not_logged_in_returns_401(self, app):
        response = app.test_client().get('/api/v2/version')
        assert response.status_code == 401


class TestApiIndexAndDocs:
    def test_api_index_redirects_to_docs(self, client):
        response = client.get('/api/v2/')
        assert response.status_code == 302
        assert response.headers['Location'] == '/api/v2/docs'

    def test_api_index_not_logged_in_redirects_to_login(self, app):
        response = app.test_client().get('/api/v2/')
        assert response.status_code == 302

    def test_docs_logged_in(self, client):
        response = client.get('/api/v2/docs')
        assert response.status_code == 200
        assert 'Swagger UI' in response.data.decode('utf-8')

    def test_docs_not_logged_in_redirects_to_login(self, app):
        response = app.test_client().get('/api/v2/docs')
        assert response.status_code == 302


class TestUnauthorizedAccess:
    def test_month_goal_distance_not_logged_in_returns_401(self, app):
        response = app.test_client().get('/api/v2/monthGoals/monthGoalDistance')
        assert response.status_code == 401
