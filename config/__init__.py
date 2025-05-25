import logging
import yaml


def load_config(config_path):
    """Завантаження конфігурації з YAML-файлу."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logging.error(f"Помилка завантаження конфігурації: {e}")
        raise

CHART_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"