import asyncio

import yaml
import logging
from src.logger import setup_logging
from src.mikrotik_api import MikrotikAPI
from src.bgp_parser import BGPParser
from src.storage import DataStorage, ChartStorage
from src.utils import levenshtein_distance, clear_routes


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
            routes_chart = ChartStorage(storage_config['output_path'], "routes")
            gateway_chart = ChartStorage(storage_config['output_path'], "gateways")

            # Збереження даних
            storage.save_data(bgp_data)
            logging.info("Дані успішно збережено")

            if previous_data:
                if previous_data["sessions"] == bgp_data["sessions"]:
                    logging.info("Змін у сессіях не відбулось")
                else:
                    logging.critical("Відбулись зміни у сессіях у інтервалі часу: -")

                routes_diff = levenshtein_distance(clear_routes(previous_data.get("routes", [])),
                                clear_routes(bgp_data.get("routes", [])))
                routes_chart.save_data(routes_diff)
                if previous_data["routes"] == bgp_data["routes"]:
                    logging.info("Змін у маршрутах не відбулось")
                else:
                    logging.critical("Відбулись зміни у маршрутах, відстань: %d",routes_diff)

                gateway_diff = levenshtein_distance(clear_routes(previous_data.get("gateways", [])),
                                clear_routes(bgp_data.get("gateways", [])))
                gateway_chart.save_data(gateway_diff)
                if previous_data["gateways"] == bgp_data["gateways"]:
                    logging.info("Змін у шлюзах не відбулось")
                else:
                    logging.critical("Відбулись зміни у шлюзах, відстань: %d",gateway_diff)

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