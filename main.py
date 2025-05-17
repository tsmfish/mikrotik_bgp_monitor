import yaml
import logging
from src.logger import setup_logging
from src.mikrotik_api import MikrotikAPI
from src.bgp_parser import BGPParser
from src.storage import DataStorage

def load_config(config_path):
    """Завантаження конфігурації з YAML-файлу."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logging.error(f"Помилка завантаження конфігурації: {e}")
        raise

def main():
    # Налаштування логування
    setup_logging()
    logging.info("Запуск програми для моніторингу BGP на MikroTik")

    # Завантаження конфігурації
    config = load_config('config/config.yaml')
    router_config = config['router']
    storage_config = config['storage']

    try:
        # Ініціалізація API
        mikrotik = MikrotikAPI(
            host=router_config['host'],
            username=router_config['username'],
            password=router_config['password'],
            port=router_config['port'],
        )

        # Ініціалізація парсера BGP
        parser = BGPParser(mikrotik)

        # Отримання BGP-даних
        bgp_data = parser.get_bgp_data()

        # Ініціалізація збереження
        storage = DataStorage(storage_config['output_path'])

        # Збереження даних
        storage.save_data(bgp_data)
        logging.info("Дані успішно збережено")

        mikrotik.close()

    except Exception as e:
        logging.error(f"Помилка виконання програми: {e}")
        raise

if __name__ == "__main__":
    main()