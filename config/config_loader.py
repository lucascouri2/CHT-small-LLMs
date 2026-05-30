import yaml
from pathlib import Path

class Config:
    _config = None
    _config_file_path = Path(__file__).resolve().parent / "config.yml"

    @classmethod
    def load_config(cls, file_path=_config_file_path):
        if cls._config is None:
            with open(file_path, "r") as f:
                cls._config = yaml.safe_load(f)
        return cls._config

    @classmethod
    def get(cls, key, default=None):
        keys = key.split(".")
        value = cls._config
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return default

    @classmethod
    def get_path(cls, key, default=None):
        return Path(__file__).resolve().parent.parent / cls.get(key, default)

    @classmethod
    def update_config(cls, key, value, file_path=None):
        file_path = file_path or cls._config_file_path
        keys = key.split(".")
        config = cls._config or cls.load_config(file_path)

        sub_config = config
        for k in keys[:-1]:
            sub_config = sub_config.setdefault(k, {})
        sub_config[keys[-1]] = value

        with open(file_path, "w") as f:
            yaml.safe_dump(config, f)

        cls._config = config