Я згенерую структурований Python-проект для підключення до маршрутизатора MikroTik RB951, отримання даних маршрутизації BGP та їх збереження. Проект використовуватиме бібліотеку `librouteros` для взаємодії з MikroTik API, що є стандартним і надійним способом автоматизації завдань на MikroTik. Дані зберігатимуться у JSON-файлі для простоти, але структуру проекту зроблено модульною, щоб ви могли легко замінити формат зберігання (наприклад, на базу даних). Проект включатиме обробку помилок, логування та конфігурацію через окремий файл.

### Структура проекту
```
mikrotik_bgp_monitor/
│
├── config/
│   └── config.yaml        # Конфігураційний файл (IP, логін, пароль, налаштування)
├── logs/
│   └── app.log            # Лог-файл для запису подій
├── src/
│   ├── __init__.py        # Порожній файл для позначення модуля
│   ├── mikrotik_api.py    # Модуль для взаємодії з MikroTik API
│   ├── bgp_parser.py      # Модуль для отримання та обробки BGP-даних
│   ├── storage.py         # Модуль для збереження даних
│   └── logger.py          # Модуль для налаштування логування
├── main.py                # Головний скрипт для запуску
├── requirements.txt       # Залежності проекту
└── README.md              # Документація проекту
```

### Опис компонентів
- **config.yaml**: Зберігає параметри підключення (IP, логін, пароль) та шляхи для збереження даних.
- **mikrotik_api.py**: Встановлює з’єднання з MikroTik RB951 через API та виконує запити.
- **bgp_parser.py**: Отримує BGP-сесії та маршрути, обробляє дані для збереження.
- **storage.py**: Зберігає отримані дані у JSON-файл.
- **logger.py**: Налаштовує логування для відстеження подій і помилок.
- **main.py**: Координує роботу модулів, запускає процес збору та збереження даних.
- **requirements.txt**: Містить необхідні бібліотеки (`librouteros`, `pyyaml`).

### Вимоги
- Python 3.8+
- MikroTik RB951 із увімкненим API (порт 8728 за замовчуванням) і налаштованим BGP.
- Доступ до маршрутизатора (IP, логін, пароль).

### Артефакти проекту

#### 1. Головний скрипт (`main.py`)
```python
import yaml
import logging
from src.logger import setup_logging
from src.mikrotik_api import MikrotikAPI
from src.bgp_parser import BGPParser
from src.storage import DataStorage

def load_config(config_path):
    """Завантаження конфігурації з YAML-файлу."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logging.error(f"Помилка завантаження конфігурації: {e}")
        raise

def main():
    # Налаштування логування
    setup_logging()
    logging.info("Запуск програми для моніторингу BGP на MikroTik RB951")

    # Завантаження конфігурації
    config = load_config('config/config.config')
    router_config = config['router']
    storage_config = config['storage']

    try:
        # Ініціалізація API
        mikrotik = MikrotikAPI(
            host=router_config['host'],
            username=router_config['username'],
            password=router_config['password'],
            port=router_config['port']
        )

        # Ініціалізація парсера BGP
        parser = BGPParser(mikrotik)

        # Отримання BGP-даних
        bgp_data = parser.get_bgp_data()

        # Ініціалізація збереження
        storage = DataStorage(storage_config['output_path'])

        # Збереження даних
        storage.save_data(bgp_data)
        logging.info("Дані успішно збережено")

    except Exception as e:
        logging.error(f"Помилка виконання програми: {e}")
        raise

if __name__ == "__main__":
    main()
```

#### 2. Конфігураційний файл (`config.yaml`)
```yaml
router:
  host: 192.168.88.1  # IP-адреса MikroTik RB951
  username: admin      # Логін
  password: your_password  # Пароль
  port: 8728          # Порт API (за замовчуванням 8728)

storage:
  output_path: data/bgp_data.json  # Шлях для збереження даних
```

#### 3. Модуль API (`mikrotik_api.py`)
```python
import logging
from librouteros import connect
from librouteros.exceptions import TrapError, FatalError

class MikrotikAPI:
    """Клас для взаємодії з MikroTik через API."""
    def __init__(self, host, username, password, port=8728):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.api = None

    def connect(self):
        """Встановлення з'єднання з маршрутизатором."""
        try:
            self.api = connect(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port
            )
            logging.info(f"Підключено до MikroTik {self.host}")
        except (TrapError, FatalError) as e:
            logging.error(f"Помилка підключення до MikroTik: {e}")
            raise

    def query(self, path, params=None):
        """Виконання запиту до API."""
        if not self.api:
            self.connect()
        try:
            return list(self.api(path, params or {}))
        except (TrapError, FatalError) as e:
            logging.error(f"Помилка запиту до {path}: {e}")
            raise

    def close(self):
        """Закриття з'єднання."""
        if self.api:
            self.api.close()
            logging.info("З'єднання з MikroTik закрито")
```

#### 4. Модуль парсингу BGP (`bgp_parser.py`)
```python
import logging
from datetime import datetime

class BGPParser:
    """Клас для отримання та обробки BGP-даних."""
    def __init__(self, mikrotik_api):
        self.api = mikrotik_api

    def get_bgp_data(self):
        """Отримання даних про BGP-сесії та маршрути."""
        try:
            # Отримання BGP-сесій
            sessions = self.api.query('/routing/bgp/session')
            # Отримання BGP-маршрутів
            routes = self.api.query('/ip/route', {'bgp': 'true'})

            # Форматування даних
            bgp_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'sessions': [
                    {
                        'name': session.get('name', ''),
                        'remote-as': session.get('remote-as', ''),
                        'remote-address': session.get('remote-address', ''),
                        'state': session.get('state', ''),
                        'uptime': session.get('uptime', ''),
                        'prefix-count': session.get('prefix-count', 0)
                    } for session in sessions
                ],
                'routes': [
                    {
                        'dst-address': route.get('dst-address', ''),
                        'gateway': route.get('gateway', ''),
                        'distance': route.get('distance', ''),
                        'bgp-as-path': route.get('bgp-as-path', ''),
                        'bgp-origin': route.get('bgp-origin', '')
                    } for route in routes
                ]
            }
            logging.info(f"Отримано {len(sessions)} сесій і {len(routes)} маршрутів")
            return bgp_data
        except Exception as e:
            logging.error(f"Помилка отримання BGP-даних: {e}")
            raise
```

#### 5. Модуль збереження (`storage.py`)
```python
import json
import logging
import os

class DataStorage:
    """Клас для збереження даних."""
    def __init__(self, output_path):
        self.output_path = output_path
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def save_data(self, data):
        """Збереження даних у JSON-файл."""
        try:
            with open(self.output_path, 'w') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info(f"Дані збережено у {self.output_path}")
        except Exception as e:
            logging.error(f"Помилка збереження даних: {e}")
            raise
```

#### 6. Модуль логування (`logger.py`)
```python
import logging
import os

def setup_logging():
    """Налаштування логування."""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'app.log')),
            logging.StreamHandler()
        ]
    )
```

#### 7. Файл залежностей (`requirements.txt`)

librouteros==3.2.1
pyyaml==6.0.1


#### 8. Документація (`README.md`)
<xaiArtifact artifact_id="91f43c1a-47db-4b19-be6e-af8bc60a82a7" artifact_version_id="9a91f094-2a9e-4cc4-8a5c-ce367ffa6ee5" title="README.md" contentType="text/markdown">
# MikroTik BGP Monitor

Проект для збору та збереження даних маршрутизації BGP з маршрутизатора MikroTik RB951 за допомогою Python.

## Вимоги
- Python 3.8+
- MikroTik RB951 із увімкненим API (порт 8728)
- Налаштований BGP на маршрутизаторі
- Доступ до маршрутизатора (IP, логін, пароль)

## Встановлення
1. Клонуйте репозиторій:
   ```bash
   git clone <repository_url>
   cd mikrotik_bgp_monitor
   ```
2. Встановіть залежності:
   ```bash
   pip install -r requirements.txt
   ```
3. Налаштуйте конфігурацію в `config/config.yaml`:
   - Вкажіть IP-адресу, логін, пароль і порт маршрутизатора.
   - Вкажіть шлях для збереження даних.

## Використання
1. Запустіть скрипт:
   ```bash
   python main.py
   ```
2. Дані BGP (сесії та маршрути) будуть збережені у JSON-файл, вказаний у `config.yaml`.
3. Логи подій записуються у `logs/app.log`.

## Структура проекту
- `config/` — конфігураційні файли
- `logs/` — логи роботи програми
- `src/` — модулі програми:
  - `mikrotik_api.py` — взаємодія з MikroTik API
  - `bgp_parser.py` — отримання та обробка BGP-даних
  - `storage.py` — збереження даних
  - `logger.py` — налаштування логування
- `main.py` — головний скрипт
- `requirements.txt` — залежності
- `README.md` — документація

## Налаштування MikroTik
1. Увімкніть API на маршрутизаторі:
   ```mikrotik
   /ip service
   set api port=8728 disabled=no
   ```
2. Переконайтеся, що BGP налаштовано:
   ```mikrotik
   /routing bgp instance
   print
   /routing bgp peer
   print
   ```
3. Дозвольте доступ до API у брандмауері:
   ```mikrotik
   /ip firewall filter
   add chain=input action=accept protocol=tcp dst-port=8728 src-address=<your_python_host>
   ```

## Обробка помилок
- Логування фіксує всі помилки (підключення, запити, збереження).
- У разі помилки програма завершується з відповідним повідомленням.

## Розширення
- Зміна формату збереження: модифікуйте `storage.py` для збереження в базу даних (наприклад, SQLite).
- Додавання моніторингу: розширте `bgp_parser.py` для перевірки стану сесій (`state=established`).
- Періодичний запуск: налаштуйте cron для регулярного виконання `main.py`.

## Ліцензія
MIT License
</xaiArtifact>

### Налаштування та запуск
1. **Встановлення залежностей**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Налаштування MikroTik**:
   - Увімкніть API:
     ```mikrotik
     /ip service
     set api port=8728 disabled=no
     ```
   - Переконайтеся, що BGP налаштовано (перевірте `/routing bgp instance` та `/routing bgp peer`).
   - Дозвольте доступ до API у брандмауері:
     ```mikrotik
     /ip firewall filter
     add chain=input action=accept protocol=tcp dst-port=8728 src-address=<your_python_host>
     ```
3. **Налаштування `config.yaml`**:
   - Замініть `your_password` на реальний пароль.
   - Переконайтеся, що IP-адреса (`192.168.88.1`) відповідає вашому RB951.
4. **Запуск**:
   ```bash
   python main.py
   ```
   Дані збережуться у `data/bgp_data.json`, а логи — у `logs/app.log`.

### Формат вихідних даних
Приклад `bgp_data.json`:
```json
{
    "timestamp": "2025-05-10T07:06:00.123456",
    "sessions": [
        {
            "name": "peer1",
            "remote-as": "65001",
            "remote-address": "192.168.1.134",
            "state": "established",
            "uptime": "3h19m56s",
            "prefix-count": 111222
        }
    ],
    "routes": [
        {
            "dst-address": "11.22.33.0/24",
            "gateway": "192.168.1.134",
            "distance": "200",
            "bgp-as-path": "65001",
            "bgp-origin": "incomplete"
        }
    ]
}
```

### Обмеження
- Проект припускає, що API MikroTik доступний і BGP налаштовано. Якщо API відключено або BGP не активний, скрипт видасть помилку.
- Збереження у JSON підходить для невеликих обсягів даних. Для великих мереж розгляньте базу даних (наприклад, SQLite).
- RB951 має обмежені ресурси, тому уникайте частих запитів до API (додайте затримки або періодичний запуск через cron).

### Розширення
- **Періодичний запуск**: Налаштуйте cron для запуску скрипта щогодини:
  ```bash
  0 * * * * /usr/bin/python3 /path/to/mikrotik_bgp_monitor/main.py >> /path/to/cron.log 2>&1
  ```
- **Моніторинг стану**: Додайте перевірку `state=established` у `bgp_parser.py` і сповіщення (наприклад, через email або Discord) при проблемах.
- **База даних**: Замініть JSON на SQLite у `storage.py` для ефективного зберігання великих обсягів даних.

### Джерела
- Документація MikroTik API: https://wiki.mikrotik.com/wiki/Manual:API
- Інформація про BGP на MikroTik: https://help.mikrotik.com/docs/display/ROS/BGP[](https://help.mikrotik.com/docs/display/ROS/BGP)
- Приклади автоматизації: https://tech.layer-x.com/mikrotik-api-python[](https://tech.layer-x.com/mikrotik-api-with-python/)

Якщо потрібні додаткові функції (наприклад, сповіщення, інтеграція з Zabbix, або підтримка IPv6), уточніть, і я розширю проект!