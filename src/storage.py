import json
import logging
import os
from datetime import datetime

from config import CHART_TIME_FORMAT


class DataStorage:
    """Клас для збереження даних."""
    def __init__(self, output_path):
        now = datetime.now()
        self.output_path = output_path.format(now.strftime("%Y%m%d"), now.strftime("%H%M%S"), "overall")
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def save_data(self, data):
        """Збереження даних у JSON-файл."""
        try:
            with open(self.output_path, 'a') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info(f"Дані збережено у {self.output_path}")
        except Exception as e:
            logging.error(f"Помилка збереження даних: {e}")
            raise


class ChartStorage:
    """Клас для збереження даних."""
    def __init__(self, output_path: str):
        self.output_path = output_path
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def save_data(self, first: float, second: float):
        """Збереження даних у CSV-файл."""
        try:
            with open(self.output_path, 'a') as f:
                f.write("{0};{1};{2};\n".format(datetime.now().strftime(CHART_TIME_FORMAT), first, second))
            logging.info(f"Дані збережено у {self.output_path}")
        except Exception as e:
            logging.error(f"Помилка збереження даних: {e}")
            raise