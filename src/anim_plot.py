import logging
import os
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import signal
import sys

class DynamicDualArrayPlot:
    """Клас для відображення графіку двох масивів із пороговими значеннями."""
    def __init__(self, shared_data, max_points=50, update_interval=5000, yellow_threshold=50, red_threshold=75, save_dir="."):
        """
        Ініціалізація графіку.
        Args:
            shared_data: Словник із даними (routes, sessions, timestamps).
            max_points: Максимальна кількість точок.
            update_interval: Інтервал оновлення (мс).
            yellow_threshold: Жовтий поріг.
            red_threshold: Червоний поріг.
            save_dir: Папка для збереження зображень графіку.
        """
        self.shared_data = shared_data
        self.max_points = max_points
        self.update_interval = update_interval
        self.yellow_threshold = yellow_threshold
        self.red_threshold = red_threshold
        self.save_dir = save_dir
        self.times = []
        self.fig, self.ax = plt.subplots()
        self.line1, = self.ax.plot([], [], 'b-', label='Кількість BGP маршрутів')
        self.line2, = self.ax.plot([], [], 'g-', label='Кількість BGP сесій')
        self.ax.axhline(y=self.yellow_threshold, color='yellow', linestyle='--', label='Жовтий поріг')
        self.ax.axhline(y=self.red_threshold, color='red', linestyle='--', label='Червоний поріг')
        self.ax.set_xlabel('Час')
        self.ax.set_ylabel('Кількість')
        self.ax.set_title('оцінка редакційної дистанції')
        self.ax.legend()
        self.ax.grid(True)

    def init_plot(self):
        matplotlib.use('agg')

        self.ax.set_xlim(0, self.max_points)
        self.ax.set_ylim(0, max(self.red_threshold + 10, 0))
        return self.line1, self.line2

    def update_plot(self, frame):
        timestamp = datetime.now().strftime("%Y%m%d %H%M%S")
        # Читання даних із shared_data
        routes = [value[0][0] for value in self.shared_data]
        sessions = [value[1][0] for value in self.shared_data]

        logging.info("routes: %s", routes)
        logging.info("sessions: %s", sessions)

        self.times = list(range(len(routes)))

        if routes and sessions:
            self.line1.set_data(self.times, routes)
            self.line2.set_data(self.times, sessions)
            self.ax.set_xlim(max(0, len(routes) - self.max_points), max(len(routes), self.max_points))
            all_data = routes + sessions
            self.ax.set_ylim(max(0, min(all_data + [self.yellow_threshold, self.red_threshold]) - 5),
                            max(all_data + [self.yellow_threshold, self.red_threshold]) + 5)
            logging.info(f"[{timestamp}] Оновлено графік: маршрутів={routes[-1] if routes else 0}, сесій={sessions[-1] if sessions else 0}")
            # Збереження графіку як зображення
            save_path = os.path.join(self.save_dir, f"plot_{timestamp}.png")
            # plt.savefig(save_path)
            # logging.info(f"[{timestamp}] Графік збережено: {save_path}")
        return self.line1, self.line2

    def run(self):
        try:
            ani = FuncAnimation(self.fig, self.update_plot, init_func=self.init_plot,
                               interval=self.update_interval, blit=True, cache_frame_data=False)
            plt.show()
        except Exception as e:
            timestamp = datetime.now().strftime("%Y%m%d %H%M%S")
            logging.error(f"[{timestamp}] Помилка: {e}")
            plt.close(self.fig)