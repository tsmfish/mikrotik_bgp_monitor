import matplotlib.pyplot as plt

# Colors
WHITE = "#ffffff"
RED = "#ff0000"
BLUE = "#0000ff"
GREEN = "#00ff00"
BLACK = "#000000"
YELLOW = "#ffff00"
TRANSPARENT = "#00000000"
NAVY_BLUE = "#000080"
TELECOM_GRAY = "#7e8282"


class LineChart:
    def __init__(self):
        plt.ion()  # Enable interactive mode

        self.fig, self.ax = plt.subplots()
        self.x1_data, self.x2_data, self.y_data = [], [], []
        self.line1, self.line2, = self.ax.plot(self.x1_data, self.x2_data, self.y_data)

        # self.line1.set_animated(True)
        # self.line1.set_color(NAVY_BLUE)
        # self.line2.set_animated(True)
        # self.line2.set_color(TELECOM_GRAY)

        self.ax.set_xlabel("час")
        self.ax.set_ylabel("відстань Левенштайна")
        self.ax.set_title("редакційна відстань зміни маршрутів")

    def update_plot(self, new_x1: int, new_x2: int):
        self.x1_data.append(new_x1)
        self.x2_data.append(new_x2)
        self.y_data.append(self.y_data[-1] if self.y_data else 0)

        self.line1.set_xdata(self.x1_data)
        self.line2.set_xdata(self.x2_data)
        self.line1.set_ydata(self.y_data)
        self.line2.set_ydata(self.y_data)

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

