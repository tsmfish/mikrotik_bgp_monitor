import plotly.graph_objects as go
import threading
import time

from config import load_config


def update_plot(routes_diff_history, stop_event):
    config = load_config('config/config.yaml')
    charts_config = config['charts']

    """Update the Plotly chart with routes_diff data."""
    fig = go.Figure()

    # Initialize the plot with empty data
    items_count = len(routes_diff_history)
    times = list(range(1, items_count + 1))
    green_bound = charts_config['green_bound']
    red_bound = charts_config['red_bound']
    routes_diff_etalon_chart = [value[0][0] for value in routes_diff_history]
    routes_diff_history_chart = [value[0][0] for value in routes_diff_history]

    # Add routes_diff trace
    fig.add_trace(go.Scatter(
        x=times,
        y=routes_diff_etalon_chart,
        mode='lines+markers',
        name='Різниця із еталонним значенням маршрутів',
        line=dict(color='#1e90ff')
    ))

    # Add routes_diff trace
    fig.add_trace(go.Scatter(
        x=times,
        y=routes_diff_history_chart,
        mode='lines+markers',
        name='Зміна таблиці маршрутів у часі',
        line=dict(color='#1e90ff')
    ))

    # Add green bound trace
    fig.add_trace(go.Scatter(
        x=times,
        y=[green_bound] * items_count,
        mode='lines',
        name='одинична відмова',
        line=dict(color='#00ff00', dash='dash')
    ))

    # Add red bound trace
    fig.add_trace(go.Scatter(
        x=times,
        y=[red_bound] * items_count,
        mode='lines',
        name='відмова обладнання',
        line=dict(color='#ff0000', dash='dash')
    ))

    # Set layout
    fig.update_layout(
        title='зміна маршрута по Левенштайну',
        xaxis_title='час',
        yaxis_title='відстань Левенштайна',
        yaxis=dict(range=[0, max(routes_diff_history_chart + [100]) + 10]),
        showlegend=True
    )

    # Show the initial plot in a separate thread to avoid blocking asyncio
    def show_plot():
        fig.show()

    threading.Thread(target=show_plot, daemon=True).start()

    # Keep updating the plot until stop_event is set
    while not stop_event.is_set():
        times = list(range(1, len(routes_diff_history_chart) + 1))

        # Update data
        fig.data[0].x = times
        fig.data[0].y = routes_diff_history_chart
        fig.data[1].x = times
        fig.data[1].y = [green_bound]
        fig.data[2].x = times
        fig.data[2].y = [red_bound]

        # Update y-axis range
        fig.update_layout(yaxis=dict(range=[0, max(routes_diff_history_chart + [100]) + 10]))

        time.sleep(5)  # Update every 5 seconds
