import matplotlib.pyplot as plt
import time

plt.ion()  # Enable interactive mode

fig, ax = plt.subplots()
x_data, y_data = [], []
line, = ax.plot(x_data, y_data)

ax.set_xlabel("X-axis")
ax.set_ylabel("Y-axis")
ax.set_title("Real-time Line Chart")

def update_plot(new_x, new_y):
    x_data.append(new_x)
    y_data.append(new_y)
    line.set_xdata(x_data)
    line.set_ydata(y_data)
    ax.relim()
    ax.autoscale_view()
    fig.canvas.draw()
    fig.canvas.flush_events()

# Example usage
for i in range(20):
    update_plot(i, i**2)
    time.sleep(0.1)