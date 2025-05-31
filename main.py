import logging
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.dates import DateFormatter
from datetime import datetime
from enum import Enum

from config import load_config, CHART_TIME_FORMAT
from src.data_reader import DataReader
from src.logger import setup_logging
from src.mikrotik_api import MikrotikAPI
from src.bgp_parser import BGPParser
from src.storage import DataStorage, ChartStorage
from src.utils import levenshtein_distance, clear_routes, clear_sessions, normalize

import asyncio
import threading

import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.withdraw()
# root.mainloop()


# --- Setup for Matplotlib Plot ---
fig, ax = plt.subplots(figsize=(16, 9))
xdata = [datetime.now()]

line1, = ax.plot(xdata, [0], 'y.-', label='різниця із еталоном', linewidth=2)
line2, = ax.plot(xdata, [0], 'ro', label='диференційна різниці')

date_formater = DateFormatter(CHART_TIME_FORMAT)
# ax.xaxis.set_major_formatter(date_formater)
# ax.xaxis.set_major_locator(HourLocator(interval=1))
# ax.xaxis.set_minor_locator(MinuteLocator(interval=1))
# ax.xaxis.set_minor_locator(SecondLocator(interval=10))
ax.set_title('Результати моніторингу маршрутної інформації')
ax.set_xlabel('час, у періодах опитування')
ax.set_ylabel('оцінка змін у одиницях відстані Левенштейна')
ax.set_ylim(-0.05, 1.05)
ax.legend()
ax.set_xticklabels([])
ax.grid(True)
plt.draw()

class Severity(Enum):
    MINOR = 0
    MAJOR = 1
    INTRUSION = 2


issue_counters: dict[Severity, int] = {
    Severity.MINOR: 0,
    Severity.MAJOR: 0,
    Severity.INTRUSION: 0,
}


def show_message(severity: Severity, title: str, message: str) -> None:
    try:
        if severity == Severity.MINOR:
            root.after(0, lambda: messagebox.showinfo(title, message))
        if severity == Severity.MAJOR:
            root.after(0, lambda: messagebox.showwarning(title, message))
        if severity == Severity.INTRUSION:
            root.after(0, lambda: messagebox.showerror(title, message))
    except RuntimeError:
        pass

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
    minor_alert = float(analyze_config['minor-alert-level'])
    major_alert = float(analyze_config['major-alert-level'])

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

        detected: dict[Severity, int | None] = {
            Severity.MINOR: None,
            Severity.MAJOR: None,
            Severity.INTRUSION: None,
        }

        global issue_counters

        seed = 0
        while True:
            # Отримання BGP-даних
            bgp_data = parser.get_bgp_data()

            # Ініціалізація збереження
            storage = DataStorage(storage_config['output_path'])

            # Збереження даних
            storage.save_data(bgp_data)
            logging.info("Дані успішно збережено")

            etalon_diff, previous_diff, gateway_diff = [0, 0, 0], [0,0,0], [0, 0, 0]

            if etalon_data:
                session_diff = levenshtein_distance(clear_sessions(etalon_data.get("sessions", [])),
                                               clear_routes(bgp_data.get("sessions", [])))

                routes_diff = levenshtein_distance(clear_routes(etalon_data.get("routes", [])),
                                                  clear_routes(bgp_data.get("routes", [])))
                gateway_diff = levenshtein_distance(etalon_data.get("gateways", []), bgp_data.get("etalon_gateways", []))

                session_diff_normalised, routes_diff_normalised, gateway_diff_normalised  = (
                    normalize(session_diff, len(etalon_data.get("sessions", []))),
                    normalize(routes_diff, len(etalon_data.get("routes", []))),
                    normalize(gateway_diff, len(etalon_data.get("gateways", []))),
                )

                etalon_diff = routes_diff

                if session_diff_normalised[0] < minor_alert:
                    pass
                else:
                    logging.critical("Сессії відмінні від еталону: -")

                if etalon_data["routes"] == bgp_data["routes"]:
                    detected[Severity.INTRUSION], detected[Severity.MINOR], detected[Severity.MAJOR] = None, None, None
                else:
                    if routes_diff_normalised[1] > minor_alert:
                        logging.critical("Виявлено нові маршрути, кількість доданих маршрутів: %d", routes_diff[1])
                        if not detected[Severity.INTRUSION]:
                            detected[Severity.INTRUSION] = seed

                    if routes_diff_normalised[0] > routes_diff_normalised[1]:
                        logging.critical("Маршрути відмінні від еталону, відстань: %d", routes_diff[0])

                    if 0 < routes_diff_normalised[2] < minor_alert:
                        logging.critical("Часткова відмова, кількість: %d", routes_diff[2])
                        if not detected[Severity.MINOR]:
                            detected[Severity.MINOR] = seed
                    elif major_alert < routes_diff[2]:
                        logging.critical("Відмова обладнання, кількість: %d", routes_diff[2])
                        if not detected[Severity.MAJOR]:
                            detected[Severity.MAJOR] = seed

                if gateway_diff[0] < minor_alert:
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
                routes_diff_normalised = normalize(routes_diff, len(previous_data.get("routes", [])))

                if previous_data["routes"] == bgp_data["routes"]:
                    if routes_diff[0] == 0:
                        logging.info("Таблиця маршрутів відновилась до еталонно")
                    else:
                        logging.info("Змін у маршрутах не відбулось")
                else:
                    logging.critical("Відбулись зміни у маршрутах, відстань: %d", routes_diff_normalised[0])

                    if detected[Severity.INTRUSION] and detected[Severity.INTRUSION] == seed:
                        show_message(Severity.INTRUSION, "Втручання", "Підозра на втручання")
                        issue_counters[Severity.INTRUSION] += 1
                    if detected[Severity.MINOR] and detected[Severity.MINOR] == seed:
                        show_message(Severity.MINOR, "Відмова", "Виникла відмова у з'єднаннях")
                        issue_counters[Severity.MINOR] += 1
                    if detected[Severity.MAJOR] and detected[Severity.MAJOR] == seed:
                        show_message(Severity.MAJOR, "Відмова", "Виникла значна відмова")
                        issue_counters[Severity.MAJOR] += 1

                previous_diff = routes_diff

                gateway_diff = levenshtein_distance(previous_data.get("gateways", []),bgp_data.get("gateways", []))
                gateway_diff_normalised = normalize(gateway_diff, len(previous_data.get("gateways", [])))

                if previous_data["gateways"] == bgp_data["gateways"]:
                    logging.info("Змін у шлюзах не відбулось")
                else:
                    logging.critical("Відбулись зміни у шлюзах, відстань: %d", gateway_diff_normalised[0])

            previous_data = bgp_data
            line_chart.save_data(
                etalon_diff[0]/max(len(etalon_data.get("routes", [])), 1),
                previous_diff[0]/max(len(previous_data.get("routes", [])), 1)
            )

            seed += 1

            await asyncio.sleep(running_config['interval'])
    except KeyboardInterrupt:
        logging.info(f"Моніторінг припинено")
        stop_event.set()
    except Exception as e:
        logging.error(f"Помилка виконання програми: {e}")
        logging.exception(e)
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
    # ax.xaxis.set_animated(True)
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
    print("Вікно графіка закрито. Сигнал зупинки зчитувача даних...")
    data_reader.stop()
    try:
        data_reader.join()
    except KeyboardInterrupt:
        pass

    print("Додаток припинено")
    logging.info(f"Статистика по сесії: \n\tвиявлено втручань: {issue_counters[Severity.INTRUSION]},\n\tвиявлено відмов: {issue_counters[Severity.MINOR]},\n\tвиявлено значних відмов: {issue_counters[Severity.MAJOR]}.")
    root.destroy()