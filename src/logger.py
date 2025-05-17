import logging
import os
from datetime import datetime


def setup_logging():
    """Налаштування логування."""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    now = datetime.now()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, '{0}_{1}_events.log'.format(now.strftime("%Y%m%d"), now.strftime("%H%M%S")))),
            logging.StreamHandler()
        ]
    )