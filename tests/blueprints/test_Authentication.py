import pytest
from flask import session

from sporttracker.logic.model.User import create_user, Language
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


@pytest.fixture()
def client(app):
    return app.test_client()


class TestAuthentication:
    def test_index_not_logged_in_should_redirect_to_login(self, client):
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert 'Login' in response.data.decode('utf-8')

    def test_url_not_logged_in_should_redirect_to_login(self, client):
        response = client.get('/workouts', follow_redirects=True)
        assert response.status_code == 200
        assert 'Login' in response.data.decode('utf-8')

    def test_login_post_no_username_should_redirect_to_login_with_error(self, client):
        response = client.post('/login', follow_redirects=True, data={})
        assert response.status_code == 200
        responseData = response.data.decode('utf-8')
        assert 'Login' in responseData
        assert 'Unknown user' in responseData

    def test_login_post_no_password_should_redirect_to_login_with_error(self, client):
        response = client.post('/login', follow_redirects=True, data={'username': TEST_USERNAME})
        assert response.status_code == 200
        responseData = response.data.decode('utf-8')
        assert 'Login' in responseData
        assert 'Password must not be empty' in responseData

    def test_login_post_invalid_password_should_redirect_to_login_with_error(self, client):
        response = client.post(
            '/login', follow_redirects=True, data={'username': TEST_USERNAME, 'password': 'abc'}
        )
        assert response.status_code == 200
        responseData = response.data.decode('utf-8')
        assert 'Login' in responseData
        assert 'Incorrect password' in responseData

    def test_login_post_correct_credentials_should_redirect_to_index(self, client):
        response = client.post(
            '/login',
            follow_redirects=True,
            data={'username': TEST_USERNAME, 'password': TEST_PASSWORD},
        )
        assert response.status_code == 200
        responseData = response.data.decode('utf-8')
        assert 'Login' not in responseData
        assert 'Workouts' in responseData

    def test_login_post_correct_credentials_case_insensitive_username_should_redirect_to_index(
        self, client
    ):
        response = client.post(
            '/login',
            follow_redirects=True,
            data={'username': TEST_USERNAME.upper(), 'password': TEST_PASSWORD},
        )
        assert response.status_code == 200
        responseData = response.data.decode('utf-8')
        assert 'Login' not in responseData
        assert 'Workouts' in responseData

    def test_login_post_correct_credentials_next_param_should_redirect_to_next_url(self, client):
        response = client.post(
            '/login',
            follow_redirects=True,
            data={
                'username': TEST_USERNAME,
                'password': TEST_PASSWORD,
                'next': 'http://localhost/plannedTours',
            },
        )
        assert response.status_code == 200
        responseData = response.data.decode('utf-8')
        assert 'Login' not in responseData
        assert 'Planned Tours' in responseData

    def test_login_post_correct_credentials_next_param_wrong_url_redirect_to_index(self, client):
        response = client.post(
            '/login',
            follow_redirects=True,
            data={
                'username': TEST_USERNAME,
                'password': TEST_PASSWORD,
                'next': 'http://example.com/plannedTours',
            },
        )
        assert response.status_code == 200
        responseData = response.data.decode('utf-8')
        assert 'Login' not in responseData
        assert 'Workouts' in responseData

    def test_logout_should_redirect_to_index(self, client):
        with client:
            response = client.post(
                '/login',
                follow_redirects=True,
                data={'username': TEST_USERNAME.upper(), 'password': TEST_PASSWORD},
            )
            assert response.status_code == 200
            responseData = response.data.decode('utf-8')
            assert 'Login' not in responseData
            assert session['_user_id'] == '2'

            response = client.get('/logout', follow_redirects=True)
            assert response.status_code == 200
            responseData = response.data.decode('utf-8')
            assert 'Login' in responseData
            assert '_user_id' not in session
