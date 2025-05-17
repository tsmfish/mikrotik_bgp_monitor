import logging
import requests
from requests.exceptions import HTTPError, ConnectionError, RequestException

class MikrotikAPI:
    """Class for interacting with MikroTik via REST API."""
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
        """Establish a connection to the MikroTik router."""
        try:
            logging.info(f"Attempting to connect to MikroTik '{self.username}'@{self.host}:{self.port}")
            self.session = requests.Session()
            self.session.auth = (self.username, self.password)
            self.session.headers.update(self.headers)
            self.session.verify = self.verify_ssl

            # Test connection by querying system identity
            response = self.session.get(f"{self.base_url}/system/identity")
            response.raise_for_status()
            logging.info(f"Connected to MikroTik {self.host}: {response.json()['name']}")
        except (TypeError, HTTPError, ConnectionError, RequestException) as e:
            logging.error(f"Failed to connect to MikroTik: {e}")
            self.session = None
            raise

    def query(self, path: str, params=None) -> list[any]:
        """Execute a query to the REST API."""
        if not self.session:
            self.connect()

        try:
            url = f"{self.base_url}/{path}"
            response = self.session.get(url, params=params or {})
            response.raise_for_status()
            data = response.json()
            # Normalize response: return list of items (mimic librouteros behavior)
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            return data if isinstance(data, list) else [data]
        except (HTTPError, ConnectionError, RequestException) as e:
            logging.error(f"Query failed for {path}: {e}")
            raise

    def close(self) -> None:
        """Close the connection."""
        if self.session:
            try:
                # Optionally, log out (REST API sessions are stateless, but good practice)
                self.session.get(f"{self.base_url}/system/logout")
                self.session.close()
                logging.info("Connection to MikroTik closed")
            except RequestException as e:
                logging.error(f"Error during logout: {e}")
            finally:
                self.session = None
