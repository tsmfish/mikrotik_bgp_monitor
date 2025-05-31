import re
from typing import Any

# RegEx для одного октету IPv4 (0-255)
octet_re = r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"

# RegEx для повної адреси IPv4
ipv4_re = rf"^{octet_re}\.{octet_re}\.{octet_re}\.{octet_re}"

# RegEx для суфікса CIDR (0-32)
cidr_re = r"(3[0-2]|[12]?[0-9]|0)"

# Комбінований патерн: IPv4/CIDR
ipv4_cidr_re = rf"{ipv4_re}/{cidr_re}$"

zero_ip_addr = "0.0.0.0"
zero_net_addr = "0.0.0.0/0"

def is_valid_ipv4_net(address: str) -> bool:
    """
    Перевіряє, чи є рядок валідною мережевою адресою IPv4 у нотації CIDR (наприклад, '192.168.1.0/24').
    Args:
        address: Рядок для перевірки (наприклад, '192.168.1.0/24').
    Returns:
        bool: True, якщо валідна адреса IPv4 CIDR, False інакше.
    """
    return True if re.match(ipv4_cidr_re, address) else False

def is_valid_ipv4_addr(address: str) -> bool:
    """
    Перевіряє, чи є рядок валідною мережевою адресою IPv4 у нотації CIDR (наприклад, '192.168.1.0/24').
    Args:
        address: Рядок для перевірки (наприклад, '192.168.1.0/24').
    Returns:
        bool: True, якщо валідна адреса IPv4 CIDR, False інакше.
    """
    return True if re.match(ipv4_re, address) else False


def levenshtein_distance(l_value: list[Any], r_value: list[Any]) -> tuple[int, int, int]:
    """
    Обчислює відстань Левенштейна між двома послідовностями.
    Args:
        l_value: Перша послідовність.
        r_value: Друга послідовність.
    Returns:
        int: Мінімальна кількість редагувань для перетворення l_value на r_value.
    """
    if l_value == r_value:
        return 0, 0, 0

    # Ініціалізація лічильників
    rows, cols = len(l_value) + 1, len(r_value) + 1
    dp = [[(0, 0, 0)] * cols for _ in range(rows)]
    for i in range(rows):
        dp[i][0] = (i, 0, i)  # Видалення для перетворення l_value[:i] у порожній рядок
    for j in range(cols):
        dp[0][j] = (j, j, 0)  # Вставка для перетворення порожнього рядка у r_value[:j]

    # Заповнення матриці
    for i in range(1, rows):
        for j in range(1, cols):
            if l_value[i - 1] == r_value[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]  # Без вартості, якщо елементи рівні
            else:
                # Видалення: +1 до відстані, +1 до видалень
                delete = (dp[i - 1][j][0] + 1, dp[i - 1][j][1], dp[i - 1][j][2] + 1)
                # Вставка: +1 до відстані, +1 до вставок
                insert = (dp[i][j - 1][0] + 1, dp[i][j - 1][1] + 1, dp[i][j - 1][2])
                # Заміна: +1 до відстані, зберігаємо вставки/видалення з попереднього
                replace = (dp[i - 1][j - 1][0] + 1, dp[i - 1][j - 1][1], dp[i - 1][j - 1][2])

                # Вибираємо операцію з мінімальною відстанню
                dp[i][j] = min(delete, insert, replace, key=lambda x: x[0])

    return dp[rows - 1][cols - 1]

def ip_addr_to_int(ip_addr: str) -> int|None:
    """
    Конвертує IP адресу у ціле число
    :param ip_addr: IP адреса
    :return: повертає цілочисельний хеш
    """
    if not is_valid_ipv4_addr(ip_addr):
        return None

    a,b,c,d = (int(x) for x in ip_addr.split("."))

    return (a << 24) + (b << 16) + (c << 8) + d

def net_addr_to_int(net_addr: str) -> int | None:
    """
    Конвертує IP адресу мережі у ціле число
    :param net_addr: IP адреса мережі
    :return: повертає цілочисельний хеш
    """

    if not is_valid_ipv4_net(net_addr):
        return None

    (address, prefix_len) =  net_addr.split("/")

    return (ip_addr_to_int(address) << 5) + int(prefix_len)

def clear_routes(routes: list[dict[str, str]]) -> list[list[str | int]]:
    return list(
        [
            route.get("dst-address", zero_net_addr),
            route.get("gateway", zero_ip_addr),
            route.get("distance", 255)
        ]
        for route in routes
    )

def clear_sessions(sessions: list[dict[str, str]]) -> list[list[str | int]]:
    return list(
        [
            session.get("local.address", zero_net_addr),
            session.get("remote.address", zero_ip_addr),
            session.get("remote.as", 0)
        ]
        for session in sessions
    )

def normalize(origin: (int, int, int), base: int) -> (float, float, float):
    """
    Нормалізація значень відповідно до кількості записів, допускає передачу 0
    :param origin: кортеж оригінальних значень
    :param base: кількість значень
    :return: повертає нормалізований кортеж
    """
    return tuple(float(value)/max(base, 1) for value in origin)