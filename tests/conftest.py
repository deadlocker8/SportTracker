import base64
import os
import threading

import pytest
from werkzeug.serving import make_server

from SportTracker import create_test_app
from TestConstants import TEST_PORT


class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = make_server('127.0.0.1', TEST_PORT, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        print('Starting test server...')
        self.server.serve_forever()

    def shutdown(self):
        print('Shutdown test server...')
        self.server.shutdown()


@pytest.fixture
def app():
    appInstance = create_test_app()
    appInstance.config.update(
        {
            'TESTING': True,
        }
    )

    yield appInstance


@pytest.fixture
def server(app):
    serverThread = ServerThread(app)
    serverThread.start()
    yield serverThread
    serverThread.shutdown()


@pytest.fixture
def firefox_options(firefox_options):
    # firefox_options.add_argument('--headless')
    return firefox_options


def pytest_selenium_capture_debug(item, report, extra):
    for log_type in extra:
        if log_type['name'] == 'Screenshot':
            imageFolderPath = os.path.join(os.path.dirname(__file__), 'screenshots')
            os.makedirs(imageFolderPath, exist_ok=True)
            imagePath = os.path.join(imageFolderPath, f'{item.name}.png')
            content = base64.b64decode(log_type['content'].encode('utf-8'))
            with open(imagePath, 'wb') as f:
                f.write(content)
