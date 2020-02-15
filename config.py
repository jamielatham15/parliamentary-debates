import pathlib
import platform
import urllib.parse
from secrets import passwd

class Config:
    path = pathlib.Path('.')
    data_path = path / 'data'
    passwd = urllib.parse.quote_plus(passwd)

class LocalConfig(Config):
    database_uri = (
        'postgresql://postgres:' + passwd + '@localhost/postgres'
        )

HOST_CONFIGS = {
    "DESKTOP-7KO9JAE": LocalConfig
}

HOST_NAME = platform.node()

if HOST_NAME in HOST_CONFIGS:
    config = HOST_CONFIGS[HOST_NAME]()
else:
    raise RuntimeError(f"Host config not found for {HOST_NAME}")