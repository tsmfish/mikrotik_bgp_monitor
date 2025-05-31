import logging
import requests
from requests.exceptions import HTTPError, ConnectionError, RequestException

class MikrotikAPI:
    """Клас для взаємодії з MikroTik через REST API."""
    def __init__(self,
                 host: str, username: str, password: str,
                 port: int=443,
                 use_ssl: bool=False, verify_ssl: bool=False):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl
        self.base_url = f"{'https' if use_ssl else 'http'}://{self.host}:{self.port}/rest"
        self.session = None
        self.headers = {"Content-Type": "application/json"}

    def connect(self) -> None:
        """Встановити з'єднання з маршрутизатором MikroTik."""
        try:
            logging.info(f"Спроба підключення до MikroTik '{self.username}'@{self.host}:{self.port}")
            self.session = requests.Session()
            self.session.auth = (self.username, self.password)
            self.session.headers.update(self.headers)
            self.session.verify = self.verify_ssl

            # Тестування з'єднання через запит системної ідентичності
            response = self.session.get(f"{self.base_url}/system/identity")
            response.raise_for_status()
            logging.info(f"Підключено до MikroTik {self.host}: {response.json()['name']}")
        except (TypeError, HTTPError, ConnectionError, RequestException) as e:
            logging.error(f"Не вдалося підключитися до MikroTik: {e}")
            self.session = None
            raise

    def query(self, path: str, params=None) -> list[any]:
        """Виконати запит до REST API."""
        if not self.session:
            self.connect()

        try:
            url = f"{self.base_url}/{path}"
            response = self.session.get(url, params=params or {})
            response.raise_for_status()
            data = response.json()
            # Нормалізація відповіді: повернення списку елементів (імітація поведінки librouteros)
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            return data if isinstance(data, list) else [data]
        except (HTTPError, ConnectionError, RequestException) as e:
            logging.error(f"Запит для {path} не виконано: {e}")
            raise

    def close(self) -> None:
        """Закрити з'єднання."""
        if self.session:
            try:
                # Опціонально, вихід із системи (сесії REST API є безстановими, але це хороша практика)
                self.session.get(f"{self.base_url}/system/logout")
                self.session.close()
                logging.info("З'єднання з MikroTik закрито")
            except RequestException as e:
                logging.error(f"Помилка під час виходу: {e}")
            finally:
                self.session = None