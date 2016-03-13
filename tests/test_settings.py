import os
import pytest
from momo.utils import utf8_encode
from momo.settings import Settings, ENV_SETTINGS_DIR, ENV_SETTINGS_FILE


def add_line(f, line=None):
    if line is None:
        f.write('\n')
    else:
        f.write(utf8_encode(line) + '\n')


@pytest.mark.usefixtures('testdir')
class TestSettings:

    @pytest.mark.usefixtures('settings_file')
    def test_settings_file(self, settings_file):
        # explicit pass arguments
        settings_dir = os.path.dirname(settings_file)
        settings = Settings(settings_dir=settings_dir,
                            settings_file=settings_file)
        assert settings.settings_dir == settings_dir
        assert settings.settings_file == settings_file

        # set environment variables
        os.environ[ENV_SETTINGS_DIR] = settings_dir
        os.environ[ENV_SETTINGS_FILE] = settings_file
        settings = Settings(settings_dir=settings_dir,
                            settings_file=settings_file)
        assert settings.settings_dir == settings_dir
        assert settings.settings_file == settings_file

        # add test settings
        with open(settings_file, 'w') as f:
            add_line(f, 'test_key: test_value')
        assert settings.load()
        assert settings.test_key == 'test_value'
