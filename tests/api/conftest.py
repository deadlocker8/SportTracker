import pytest

from sporttracker.SportTracker import create_test_app
from sporttracker.user.UserEntity import Language, User, create_user
from tests.TestConstants import TEST_PASSWORD, TEST_USERNAME


@pytest.fixture
def app(tmp_path):
    appInstance = create_test_app(str(tmp_path / 'data'))
    appInstance.config.update(
        {
            'TESTING': True,
        }
    )

    yield appInstance


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)


@pytest.fixture
def client(app):
    testClient = app.test_client()
    response = testClient.post('/api/v2/login', data={'username': TEST_USERNAME, 'password': TEST_PASSWORD})
    assert response.status_code == 200
    return testClient


@pytest.fixture
def user(app):
    with app.app_context():
        user = User.query.filter(User.username == TEST_USERNAME).first()
        if user is None:
            raise ValueError(f'Could not find user with username {TEST_USERNAME}')
        return user
