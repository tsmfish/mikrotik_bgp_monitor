import logging
from datetime import datetime

class BGPParser:
    """Клас для отримання та обробки BGP-даних."""
    def __init__(self, mikrotik_api):
        self.api = mikrotik_api

    def get_bgp_data(self):
        """Отримання даних про BGP-сесії та маршрути."""
        try:
            # Отримання BGP-шаблонів (процесів)
            bgp_processes = self.api.query('routing/bgp/template', params={"disabled": "false"})
            # Отримання BGP-сесій
            sessions = self.api.query("routing/bgp/connection")
            # Отримання BGP-маршрутів
            routes = self.api.query("ip/route", params={"bgp": "true", "active": "true"})

            # Форматування даних
            bgp_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'sessions': [
                    {
                        'name': session.get('name', ''),
                        'as': session.get('as', ''),
                        'router-id': session.get('router-id', ''),
                        'local.address': session.get('local.address', ''),
                        'remote.as': session.get('remote.as', ''),
                        'remote.address': session.get('remote.address', ''),
                    } for session in sessions
                ],
                'routes': [
                    {
                        'router-id': bgp_processes[0].get('router-id', ''),
                        'dst-address': route.get('dst-address', ''),
                        'gateway': route.get('gateway', ''),
                        'distance': route.get('distance', ''),
                    } for route in routes
                ],
                'gateways': list(set(route.get('gateway', '') for route in routes)),
            }
            logging.info(f"Отримано {len(sessions)} сесій і {len(routes)} маршрутів")
            return bgp_data
        except Exception as e:
            logging.error(f"Помилка отримання BGP-даних: {e}")
            raise