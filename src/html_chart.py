import logging
import os


def create_html_chart(output_path):
    """Create an HTML file with Plotly for real-time routes_diff visualization."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Routes Difference Chart</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #chart { max-width: 800px; height: 500px; }
        </style>
    </head>
    <body>
        <h2>Routes Difference Over Time</h2>
        <div id="chart"></div>
        <script>
            function updateChart() {
                fetch('routes_diff.json')
                    .then(response => response.json())
                    .then(data => {
                        const times = data.map((_, i) => i + 1);
                        const greenBound = Array(data.length).fill(50); // Static green bound
                        const redBound = Array(data.length).fill(100); // Static red bound
                        const trace1 = {
                            x: times,
                            y: data,
                            mode: 'lines+markers',
                            name: 'Routes Difference',
                            line: { color: '#1e90ff' }
                        };
                        const trace2 = {
                            x: times,
                            y: greenBound,
                            mode: 'lines',
                            name: 'Green Bound (50)',
                            line: { color: '#00ff00', dash: 'dash' }
                        };
                        const trace3 = {
                            x: times,
                            y: redBound,
                            mode: 'lines',
                            name: 'Red Bound (100)',
                            line: { color: '#ff0000', dash: 'dash' }
                        };
                        const layout = {
                            title: 'Routes Difference Over Time',
                            xaxis: { title: 'Time (Interval)' },
                            yaxis: { title: 'Routes Difference', range: [0, Math.max(...data, 100) + 10] },
                            showlegend: true
                        };
                        Plotly.newPlot('chart', [trace1, trace2, trace3], layout);
                    })
                    .catch(error => console.error('Error fetching data:', error));
            }

            setInterval(updateChart, 5000); // Update every 5 seconds
            updateChart(); // Initial update
        </script>
    </body>
    </html>
    """
    html_path = os.path.join(output_path, "chart.html")
    with open(html_path, 'w') as f:
        f.write(html_content)
    logging.info(f"HTML chart created at {html_path}")