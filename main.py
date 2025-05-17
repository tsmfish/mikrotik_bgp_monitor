import asyncio

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

async def main():
    # Налаштування логування
    setup_logging()
    logging.info("Запуск програми для моніторингу BGP на MikroTik")

    # Завантаження конфігурації
    config = load_config('config/config.yaml')
    router_config = config['router']
    storage_config = config['storage']
    running_config = config['running']

    # Ініціалізація API
    mikrotik = MikrotikAPI(
        host=router_config['host'],
        username=router_config['username'],
        password=router_config['password'],
        port=router_config['port'],
    )

    # Ініціалізація парсера BGP
    parser = BGPParser(mikrotik)

    try:
        previous_data = {}
        logging.info(f"Моніторінг розпочато")
        while True:
            # Отримання BGP-даних
            bgp_data = parser.get_bgp_data()

            # Ініціалізація збереження
            storage = DataStorage(storage_config['output_path'])

            # Збереження даних
            storage.save_data(bgp_data)
            logging.info("Дані успішно збережено")

            if previous_data:
                if previous_data["sessions"] == bgp_data["sessions"]:
                    logging.info("Змін у сессіях не відбулось")
                else:
                    logging.critical("Відбулись зміни у сессіях")
                if previous_data["routes"] == bgp_data["routes"]:
                    logging.info("Змін у маршрутах не відбулось")
                else:
                    logging.critical("Відбулись зміни у маршрутах")

            previous_data = bgp_data

            await asyncio.sleep(running_config['interval'])

    except KeyboardInterrupt:
        logging.info(f"Моніторінг припинено")
    except Exception as e:
        logging.error(f"Помилка виконання програми: {e}")
    finally:
        mikrotik.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(f"Моніторінг припинено")