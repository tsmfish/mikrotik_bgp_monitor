import logging
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime
import asyncio

from matplotlib.dates import DateFormatter

from config import load_config, CHART_TIME_FORMAT
from src.data_reader import DataReader
from src.logger import setup_logging
from src.mikrotik_api import MikrotikAPI
from src.bgp_parser import BGPParser
from src.storage import DataStorage, ChartStorage
from src.utils import levenshtein_distance, clear_routes
import threading


# --- Setup for Matplotlib Plot ---
fig, ax = plt.subplots(figsize=(16, 9))
xdata = [datetime.now()]

line1, = ax.plot(xdata, [0], 'y.-', label='різниця із еталоном', linewidth=2)
line2, = ax.plot(xdata, [0], 'ro', label='диференційна різниці')

date_formater = DateFormatter(CHART_TIME_FORMAT)
ax.xaxis.set_major_formatter(date_formater)
# ax.xaxis.set_major_locator(HourLocator(interval=1))
# ax.xaxis.set_minor_locator(MinuteLocator(interval=1))
# ax.xaxis.set_minor_locator(SecondLocator(interval=10))
ax.set_title('Результати моніторингу маршрутної інформації')
ax.set_xlabel('час')
ax.set_ylabel('оцінка змін у одиницях відстані Левенштейна')
ax.set_ylim(-0.5, 10)
ax.legend()
ax.set_xticklabels([])
ax.grid(True)

async def bgp_observer(chart_file: str):
    # Налаштування логування
    setup_logging()
    logging.info("Запуск програми для моніторингу BGP на MikroTik")

    # Завантаження конфігурації
    global config
    router_config = config['router']
    storage_config = config['storage']
    running_config = config['running']
    analyze_config = config['analyze']
    minor_alert = analyze_config['minor-alert-level']
    major_alert = analyze_config['major-alert-level']

    # Ініціалізація API
    mikrotik = MikrotikAPI(
        host=router_config['host'],
        username=router_config['username'],
        password=router_config['password'],
        port=router_config['port'],
    )

    # Ініціалізація парсера BGP
    parser = BGPParser(mikrotik)

    stop_event = threading.Event()
    try:
        etalon_data: dict[str, Any] = {}
        previous_data: dict[str, Any] = {}
        logging.info(f"Моніторінг розпочато")
        line_chart = ChartStorage(chart_file)

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
                    if routes_diff[1] > 0:
                        logging.critical("Виявлено нові маршрути, кількість доданих маршрутів: %d", routes_diff[1])

                    if routes_diff[0] > routes_diff[1]:
                        logging.critical("Маршрути відмінні від еталону, відстань: %d", routes_diff[0])

                    if 0 < routes_diff[2] < minor_alert:
                        logging.critical("Часткова відмова, кількість: %d", routes_diff[2])
                    elif minor_alert < routes_diff[2]:
                        logging.critical("Відмова обладнання, кількість: %d", routes_diff[2])


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
                    if etalon_diff[0] == 0:
                        logging.info("Таблиця маршрутів відновилась до еталонно")
                    else:
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
        stop_event.set()
    except Exception as e:
        logging.error(f"Помилка виконання програми: {e}")
        stop_event.set()
    finally:
        mikrotik.close()

def update_plot(frame):
    global data_reader

    current_data = data_reader.get_data()
    global config
    max_points = config['charts']['max_records']

    if current_data['timestamps']:
        data_size = len(current_data['timestamps'])
        if data_size <= max_points:
            xdata = current_data['timestamps']
            ydata1 = current_data['values1']
            ydata2 = current_data['values2']
        else:
            xdata = current_data['timestamps'][data_size-max_points:]
            ydata1 = current_data['values1'][data_size-max_points:]
            ydata2 = current_data['values2'][data_size-max_points:]
    else:
        xdata = [datetime.now()]
        ydata1 = [0]
        ydata2 = [0]

    line1.set_data(xdata, ydata1)
    line2.set_data(xdata, ydata2)

    ax.relim()
    ax.autoscale_view(True, True, True)
    fig.autofmt_xdate()

    return line1, line2,


if __name__ == "__main__":
    config = load_config('config/config.yaml')
    now = datetime.now()
    output_path = config['storage']['chart_path'].format(now.strftime("%Y%m%d"), now.strftime("%H%M%S"))

    # Wrapper function to run the async task in a separate thread
    def run_async_in_thread(loop, coro):
        asyncio.set_event_loop(loop) # Set the loop for this thread
        loop.run_until_complete(coro) # Run the coroutine until it completes (or is cancelled)

    # Create a new event loop for the async writer thread
    new_loop = asyncio.new_event_loop()
    observer_thread = threading.Thread(
        target=run_async_in_thread,
        args=(new_loop, bgp_observer(output_path)),
        daemon=True
    )
    observer_thread.start()
    # --- End of async dummy file creation ---

    # 1. Initialize and Start the Data Reader Thread (remains synchronous for file reading)
    data_reader = DataReader(filename=output_path, interval=config['running']['interval'])
    data_reader.start()

    # 2. Set up the Matplotlib Animation
    ani = animation.FuncAnimation(fig, update_plot, interval=config['running']['interval'] * 1000, blit=True)

    # 3. Show the plot (this will block the main thread until the window is closed)
    print("Початок побудови графіка. Закрийте вікно побудови графіка, щоб зупинити програму.")

    try:
        plt.show()
    except KeyboardInterrupt:
        logging.info(f"Моніторінг припинено")

    # 4. Once the plot window is closed, signal the reader thread to stop
    print("Plot window closed. Signaling data reader to stop...")
    data_reader.stop()
    data_reader.join()
    print("Application finished.")