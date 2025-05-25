import threading
import time
from datetime import datetime

from config import CHART_TIME_FORMAT


# --- DataReader class (as provided previously) ---
class DataReader(threading.Thread):
    def __init__(self, filename, interval=5):
        super().__init__()
        self.filename = filename
        self.interval = interval
        self.running = True
        self.data_points = {'timestamps': [], 'values1': [], 'values2': []}
        self.lock = threading.Lock()

    def run(self):
        print(f"Data reader thread started for file: {self.filename}")
        last_read_byte = 0
        while self.running:
            try:
                with open(self.filename, 'r') as f:
                    f.seek(last_read_byte)
                    new_lines = f.readlines()
                    last_read_byte = f.tell()

                for line in new_lines:
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split(';')
                    if len(parts) >= 3:
                        try:
                            timestamp_str = parts[0].strip()
                            dt_object = datetime.strptime(timestamp_str, CHART_TIME_FORMAT)

                            val1 = int(parts[1].strip())
                            val2 = int(parts[2].strip())

                            with self.lock:
                                self.data_points['timestamps'].append(dt_object)
                                self.data_points['values1'].append(val1)
                                self.data_points['values2'].append(val2)

                        except (ValueError, IndexError) as e:
                            print(f"Error parsing line: '{line}' - {e}")
                    else:
                        print(f"Skipping malformed line: '{line}'")

            except FileNotFoundError:
                print(f"File not found: {self.filename}. Waiting...")
            except Exception as e:
                print(f"An error occurred in data reader thread: {e}")

            time.sleep(self.interval)

    def stop(self):
        self.running = False
        print("Data reader thread signaled to stop.")

    def get_data(self):
        with self.lock:
            return {
                'timestamps': list(self.data_points['timestamps']),
                'values1': list(self.data_points['values1']),
                'values2': list(self.data_points['values2'])
            }
