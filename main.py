import asyncio
import logging
from typing import Any

from config import load_config
from src.logger import setup_logging
from src.mikrotik_api import MikrotikAPI
from src.bgp_parser import BGPParser
from src.plot import LineChart
from src.storage import DataStorage, ChartStorage
from src.utils import levenshtein_distance, clear_routes
import threading

routes_diff_history: list[tuple[tuple[int, int, int],tuple[int, int, int]]] = []

async def bgp_observer():
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

    # Initialize routes_diff history and stop event for plotting

    stop_event = threading.Event()

    try:
        etalon_data: dict[str, Any] = {}
        previous_data: dict[str, Any] = {}
        logging.info(f"Моніторінг розпочато")
        line_chart = ChartStorage(storage_config['chart_path'])

        while True:
            # Отримання BGP-даних
            bgp_data = parser.get_bgp_data()

            # Ініціалізація збереження
            storage = DataStorage(storage_config['output_path'])

            # Збереження даних
            storage.save_data(bgp_data)
            logging.info("Дані успішно збережено")

            etalon_diff, previous_diff = [0, 0, 0], [0,0,0]

            if etalon_data:
                if etalon_data["sessions"] == bgp_data["sessions"]:
                    pass
                else:
                    logging.critical("Сессії відмінні від еталону: -")

                routes_diff = levenshtein_distance(clear_routes(etalon_data.get("routes", [])),
                                                  clear_routes(bgp_data.get("routes", [])))
                # routes_chart.save_data(routes_diff)
                etalon_diff = routes_diff

                if etalon_data["routes"] == bgp_data["routes"]:
                    pass
                else:
                    logging.critical("Маршрути відмінні від еталону, відстань: %d", routes_diff[0])

                gateway_diff = levenshtein_distance(etalon_data.get("gateways", []), bgp_data.get("etalon_gateways", []))

                if etalon_data["gateways"] == bgp_data["gateways"]:
                    pass
                else:
                    logging.critical("Відбулись зміни у шлюзах, відстань: %d", gateway_diff[0])
            else:
                etalon_data = bgp_data


            if previous_data:
                if previous_data["sessions"] == bgp_data["sessions"]:
                    logging.info("Змін у сессіях не відбулось")
                else:
                    logging.critical("Відбулись зміни у сессіях у інтервалі часу: -")

                routes_diff = levenshtein_distance(clear_routes(previous_data.get("routes", [])),
                                                  clear_routes(bgp_data.get("routes", [])))

                previous_diff = routes_diff

                if previous_data["routes"] == bgp_data["routes"]:
                    logging.info("Змін у маршрутах не відбулось")
                else:
                    logging.critical("Відбулись зміни у маршрутах, відстань: %d", routes_diff[0])

                gateway_diff = levenshtein_distance(previous_data.get("gateways", []),bgp_data.get("gateways", []))
                # gateway_chart.save_data(gateway_diff)
                if previous_data["gateways"] == bgp_data["gateways"]:
                    logging.info("Змін у шлюзах не відбулось")
                else:
                    logging.critical("Відбулись зміни у шлюзах, відстань: %d", gateway_diff[0])

            previous_data = bgp_data
            line_chart.save_data(etalon_diff[0], previous_diff[0])

            await asyncio.sleep(running_config['interval'])

    except KeyboardInterrupt:
        logging.info(f"Моніторінг припинено")
        stop_event.set()  # Signal the plot thread to stop
    except Exception as e:
        logging.error(f"Помилка виконання програми: {e}")
        stop_event.set()
    finally:
        mikrotik.close()
        stop_event.set()

if __name__ == "__main__":
    try:
        asyncio.run(bgp_observer())
    except KeyboardInterrupt:
        logging.info(f"Моніторінг припинено")
