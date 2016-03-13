import os
import pytest
import shutil
from momo.utils import mkdir_p


TEST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, '__tests__'))


@pytest.fixture
def testdir(request):
    mkdir_p(TEST_DIR)

    @request.addfinalizer
    def cleanup():
        shutil.rmtree(TEST_DIR)


@pytest.fixture(scope="module")
def settings_file(request):
    """Set up settings directory and file."""
    settings_d = os.path.join(TEST_DIR, 'momo')
    settings_f = os.path.join(settings_d, 'settings.yml')

    mkdir_p(settings_d)
    open(settings_f, 'a').close()

    @request.addfinalizer
    def cleanup():
        if os.path.exists(settings_d):
            shutil.rmtree(settings_f)

    return settings_f
