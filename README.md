MikroTik BGP Monitor
Проект для збору та збереження даних маршрутизації BGP з маршрутизатора MikroTik RB951 за допомогою Python.
Вимоги

Python 3.8+
MikroTik RB951 із увімкненим API (порт 8728)
Налаштований BGP на маршрутизаторі
Доступ до маршрутизатора (IP, логін, пароль)

Встановлення

Клонуйте репозиторій:git clone <repository_url>
cd mikrotik_bgp_monitor


Встановіть залежності:pip install -r requirements.txt


Налаштуйте конфігурацію в config/config.yaml:
Вкажіть IP-адресу, логін, пароль і порт маршрутизатора.
Вкажіть шлях для збереження даних.



Використання

Запустіть скрипт:python main.py


Дані BGP (сесії та маршрути) будуть збережені у JSON-файл, вказаний у config.yaml.
Логи подій записуються у logs/app.log.

Структура проекту

config/ — конфігураційні файли
logs/ — логи роботи програми
src/ — модулі програми:
mikrotik_api.py — взаємодія з MikroTik API
bgp_parser.py — отримання та обробка BGP-даних
storage.py — збереження даних
logger.py — налаштування логування


main.py — головний скрипт
requirements.txt — залежності
README.md — документація

Налаштування MikroTik

Увімкніть API на маршрутизаторі:/ip service
set api port=8728 disabled=no


Переконайтеся, що BGP налаштовано:/routing bgp instance
print
/routing bgp peer
print


Дозвольте доступ до API у брандмауері:/ip firewall filter
add chain=input action=accept protocol=tcp dst-port=8728 src-address=<your_python_host>



Обробка помилок

Логування фіксує всі помилки (підключення, запити, збереження).
У разі помилки програма завершується з відповідним повідомленням.

Розширення

Зміна формату збереження: модифікуйте storage.py для збереження в базу даних (наприклад, SQLite).
Додавання моніторингу: розширте bgp_parser.py для перевірки стану сесій (state=established).
Періодичний запуск: налаштуйте cron для регулярного виконання main.py.

Ліцензія
MIT License
