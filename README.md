# BOFAMET – Инфраструктура Сбора Данных и Управления

BOFAMET представляет собой комплексное решение для сбора данных с целевых систем, состоящее из модуля-коллектора (стиллера) и централизованной панели управления (C2-сервера). Коллектор, написанный на Python, компилируется в автономный исполняемый файл Windows, а собранные данные передаются на C2-сервер, разработанный на базе FastAPI.

## I. Модуль Коллектора Данных (Стиллер)

Модуль коллектора предназначен для всестороннего сбора информации с компрометированной системы.

### Ключевые Возможности:

*   **Извлечение Данных Браузеров:**
    *   Получение сохраненных учетных данных для входа (логины, пароли) из широкого спектра веб-браузеров (Chrome, Edge, Opera, Yandex, Brave, Vivaldi, Slimjet, Falkon, SeaMonkey, Maxthon, Pale Moon, Qutebrowser, Iridium, CentBrowser, Tor).
    *   Сбор файлов cookie браузеров для потенциального обхода аутентификации.
    *   Извлечение истории посещений и данных автозаполнения форм из поддерживаемых браузеров.
*   **Сбор Системной Информации:** Детальный сбор сведений о хост-системе, включая:
    *   Операционная система (тип, версия).
    *   Аппаратное обеспечение (процессор, количество ядер, объем оперативной памяти, информация о дисковом пространстве).
    *   Конфигурация сети (локальный IP-адрес, MAC-адрес, данные Wi-Fi SSID и BSSID).
    *   Информация о пользователе (имя пользователя, имя компьютера).
    *   Определение публичного IP-адреса и геолокационных данных (город, регион, страна, широта, долгота).
*   **Снимок Экрана Рабочего Стола:** Создание скриншота текущего рабочего стола целевой системы.
*   **Извлечение Сессии Telegram:** Попытка получения файлов локальной сессии Telegram (путем временного завершения процесса Telegram для обеспечения доступа к файлам сессии).
*   **Обнаружение Токенов Discord:** Сканирование системы на наличие токенов аутентификации Discord в различных расположениях.
*   **Конфигурация Steam:** Копирование конфигурационных файлов клиента Steam.
*   **Целевая Эксфильтрация Файлов:** Поиск и копирование файлов с определенными расширениями (.doc, .docx, .xls, .xlsx, .ppt, .pptx, .pdf, .bmp) из пользовательских директорий.
*   **Извлечение Криптокошельков:** Выявление и копирование файлов, ассоциированных с криптографическими кошельками (например, `wallet.dat`, `key.json`, `keystore`, `mnemonic.txt`, `seed.txt`, а также SSH-ключи, такие как `id_rsa`).
*   **Передача Данных:** Архивирование всех собранных данных в ZIP-архивы (с возможностью разделения на части при превышении заданного размера) и последующая их отправка на настроенный C2-сервер вместе с системной информацией и геолокационными данными.

## II. Модуль Билдера Коллектора

Билдер предназначен для создания настраиваемого исполняемого файла коллектора.

### Ключевые Возможности:

*   **Конфигурация C2-Сервера:** Интерактивное задание IP-адреса и порта центрального сервера управления, на который будут отправляться собранные данные.
*   **Компиляция в EXE:** Использование PyInstaller для создания единого, автономного исполняемого файла Windows (.exe) без консольного окна.
*   **Настройка Иконки:** Возможность добавления пользовательского файла иконки (.ico) к генерируемому исполняемому файлу.
*   **Многоуровневая Обфускация:** Применение нескольких слоев обфускации к исходному коду коллектора перед компиляцией для усложнения анализа:
    *   Кодирование Base16.
    *   Компиляция в байт-код Python и сериализация с использованием модуля `marshal`.
    *   Сжатие сериализованных данных с помощью библиотеки `zlib`.
    *   Кодирование сжатых данных с использованием Base32.
    *   Дополнительный слой обфускации с использованием `openobf.dll` для повышения устойчивости к реверс-инжинирингу.
*   **Логирование Процесса Сборки:** Все этапы процесса сборки, включая вывод PyInstaller, фиксируются в файле `builder_log.txt` для отладки и аудита.

## III. Центральный Сервер Управления (C2-Сервер)

C2-сервер представляет собой веб-панель на базе FastAPI для приема, хранения и управления собранными данными.

### Ключевые Возможности:

*   **Веб-Интерфейс:** Интуитивно понятный веб-интерфейс для просмотра и управления полученными логами.
*   **Защита Доступа:**
    *   **Аутентификация:** Защищенный вход в административную панель с использованием настраиваемых учетных данных.
    *   **Привязка Сессии к IP-адресу:** Сессия пользователя привязывается к его IP-адресу, обеспечивая выход из системы при обнаружении смены IP-адреса.
    *   **Защита от Bruteforce (Локальная):** Блокировка IP-адреса на 5 минут после 5 некорректных попыток входа с одного и того же IP-адреса.
    *   **Защита от Bruteforce (Глобальная):** В случае 100 глобальных неудачных попыток входа (с разных IP-адресов) панель управления будет перманентно заблокирована до перезапуска сервера.
    *   **Отключение Документации API:** Доступ к стандартной документации FastAPI (Swagger UI, ReDoc) полностью отключен для повышения безопасности и предотвращения несанкционированного изучения структуры API.
*   **Управление Логами:**
    *   **Просмотр Логируемых Событий:** Отображение списка всех полученных логов, включая временные метки, IP-адреса, имена компьютеров и другую метаинформацию.
    *   **Загрузка Отдельных Лог-Файлов:** Возможность загрузки каждого отдельного ZIP-архива с данными.
    *   **Массовая Загрузка Лог-Файлов:** Функция для скачивания всех собранных логов в едином ZIP-архиве.
    *   **Удаление Дубликатов:** При получении нового лога от уже известной пары "имя компьютера - публичный IP-адрес", предыдущая запись и связанные с ней файлы автоматически удаляются, заменяясь новой записью.
*   **Обработка Загружаемых Файлов:**
    *   **Фильтрация по Типу:** Эндпоинт загрузки данных (`/upload`) принимает только ZIP-арархивы, отклоняя любые другие типы файлов.
    *   **Организация Хранения:** Каждый загруженный лог сохраняется в отдельную директорию на сервере.
*   **Просмотр Лог-Файла Сервера:** Доступ к содержимому файла `nohup.out` (серверный лог) через веб-интерфейс для мониторинга работы сервера.
*   **Защита Отладочной Консоли (Клиентская):** Внедрение JavaScript-кода на клиентской стороне для затруднения использования отладочной консоли браузера, включая отключение контекстного меню, обнаружение нажатий F12 и Ctrl+Shift+I/J, а также бесконечный цикл `debugger;` и блокировку вывода в консоль.

## IV. Инструкции по Установке и Эксплуатации

### 1. Установка и Конфигурация C2-Сервера:

Сервер может быть установлен на системах под управлением Linux или Windows.

**Предварительные Требования:**
*   Желательная операционная система: Ubuntu 20.04.
*   Установленный Python 3.x (рекомендуется Python 3.8 или новее).
*   Утилита `pip` для установки пакетов Python.

**Порядок Установки (Linux, рекомендуется):**
1.  **Обновление Системы и Установка Python:** Выполните скрипт `Start.sh` из директории сервера. Он автоматически обновит систему, установит Python3 и pip3.
    ```bash
    chmod +x Start.sh
    sudo ./Start.sh
    ```
2.  **Настройка Сервера:** Скрипт `Start.sh` запустит `Config_C2.py`. Следуйте инструкциям командной строки:
    *   Вам будет предложено ввести желаемое имя пользователя и пароль для доступа к административной панели C2.
    *   Необходимо будет указать порт, на котором будет прослушиваться сервер (например, `8000`).
    *   Скрипт сгенерирует секретный ключ для сессий и сохранит все настройки в файл `config.json`.
    *   После настройки `Config_C2.py` предложит варианты запуска сервера (в отладочном режиме на переднем плане или в фоновом режиме с `nohup`). Для продакшн-использования рекомендуется фоновый режим.

**Порядок Установки (Windows):**
1.  **Установка Зависимостей:** Убедитесь, что у вас установлен Python 3.x и `pip`. Перейдите в корневую директорию сервера (где находится `requirements.txt`) и установите необходимые библиотеки:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Настройка Сервера:** Запустите скрипт `Config_C2.py`:
    ```bash
    python Config_C2.py
    ```
    *   Следуйте тем же инструкциям, что и для Linux, по вводу имени пользователя, пароля и порта. `config.json` будет создан автоматически.
3.  **Запуск Сервера:** После завершения `Config_C2.py`, вам будет предложено запустить сервер. Выберите желаемый режим запуска.

**Доступ к Панели Управления:**
После успешного запуска сервера, доступ к административной панели осуществляется через веб-браузер по адресу `http://<IP_ВАШЕГО_СЕРВЕРА>:<ПОРТ>/login`.

### 2. Создание Модуля Коллектора (Стиллер) с Помощью Билдера:

**Предварительные Требования:**
*   Установленный Python 3.x (рекомендуется Python 3.8+).
*   Установленные пакеты Python. Перейдите в директорию билдера и выполните:
    ```bash
    pip install PyInstaller colorama Pillow pycryptodome pypiwin32 psutil requests aiofiles pystyle pywin32
    ```
    *(Примечание: `pypiwin32` может быть заменен на `pywin32` в зависимости от версии Python и OS).*

**Порядок Создания:**
1.  **Запуск Билдера:** Запустите скрипт `BOFAMET2.py`:
    BOFAMET_C2_builder.exe
    Либо в случае использования исходного кода:
    ```bash
    python BOFAMET2.py
    ```
    *   При необходимости скрипт запросит права администратора для работы с временными файлами и PyInstaller.
2.  **Конфигурация Сборки:** Следуйте интерактивным инструкциям:
    *   Введите IP-адрес вашего развернутого C2-сервера (тот же, что вы использовали при настройке сервера).
    *   Введите порт вашего C2-сервера.
    *   При желании укажите полный путь к файлу `.ico` для использования в качестве иконки для генерируемого исполняемого файла.
3.  **Процесс Сборки:** Билдер автоматически обфусцирует исходный код коллектора и скомпилирует его в исполняемый файл с использованием PyInstaller.
4.  **Результат:** Готовый исполняемый файл под названием `BOFAMET_BUILD.exe` будет расположен в директории `dist` относительно места запуска билдера.

## V. Принцип Обфускации Коллектора:

Билдер применяет многоэтапный подход к обфускации исходного кода коллектора для обеспечения его защиты:
1.  Исходный код сначала подвергается кодированию с использованием Base16.
2.  Полученный результат компилируется в байт-код Python и сериализуется с помощью модуля `marshal`.
3.  Сериализованные данные затем сжимаются с использованием библиотеки `zlib`.
4.  Сжатые данные кодируются с помощью Base32.
5.  В качестве завершающего этапа применяется дополнительный слой кастомной обфускации, реализуемой через динамическую библиотеку `openobf.dll`.
Во время исполнения коллектора небольшой загрузчик последовательно декодирует и декомпрессирует эти слои, чтобы выполнить оригинальный код.

---
**Дисклеймер:** Данное программное обеспечение предоставляется исключительно в образовательных и исследовательских целях. Разработчики не несут ответственности за любое неправомерное использование этого инструмента. 


EN-manual

# BOFAMET – Data Collection and Control Infrastructure

BOFAMET is a comprehensive solution for collecting data from target systems, consisting of a collector module (stealer) and a centralized command and control (C2) server. The collector, written in Python, is compiled into a standalone Windows executable, and the collected data is transmitted to the C2 server, developed using FastAPI.

## I. Data Collector Module (Stealer)

The collector module is designed for comprehensive information gathering from a compromised system.

### Key Features:

*   **Browser Data Extraction:**
    *   Retrieves saved login credentials (usernames, passwords) from a wide range of web browsers (Chrome, Edge, Opera, Yandex, Brave, Vivaldi, Slimjet, Falkon, SeaMonkey, Maxthon, Pale Moon, Qutebrowser, Iridium, CentBrowser, Tor).
    *   Collects browser cookie files for potential authentication bypass.
    *   Extracts browsing history and autofill form data from supported browsers.
*   **System Information Collection:** Detailed gathering of information about the host system, including:
    *   Operating System (type, version).
    *   Hardware (processor, core count, RAM, disk space information).
    *   Network configuration (local IP address, MAC address, Wi-Fi SSID, and BSSID data).
    *   User information (username, computer name).
    *   Public IP address identification and geolocation data (city, region, country, latitude, longitude).
*   **Desktop Screenshot:** Captures an image of the current desktop of the target system.
*   **Telegram Session Extraction:** Attempts to retrieve local Telegram session files (by forcibly terminating the Telegram process to gain access to session files).
*   **Discord Token Discovery:** Scans the system for Discord authentication tokens in various locations.
*   **Steam Configuration:** Copies configuration files of the Steam client.
*   **Targeted File Exfiltration:** Searches for and steals files with specific extensions (.doc, .docx, .xls, .xlsx, .ppt, .pptx, .pdf, .bmp) from user directories.
*   **Crypto Wallet Extraction:** Identifies and copies files associated with cryptocurrency wallets (e.g., `wallet.dat`, `key.json`, `keystore`, `mnemonic.txt`, `seed.txt`, as well as SSH keys like `id_rsa`).
*   **Data Transmission:** Archives all collected data into ZIP files (partitioning into parts if necessary due to size limits) and subsequently transmits them, along with system information and geolocation data, to the configured C2 server.

## II. Collector Builder Module

The builder is designed to create a customizable executable file for the collector.

### Key Features:

*   **C2 Server Configuration:** Interactive setting of the IP address and port of the central control server to which collected data will be sent.
*   **EXE Compilation:** Uses PyInstaller to create a single, self-contained Windows executable (.exe) without a console window.
*   **Icon Customization:** Ability to add a custom icon file (.ico) to the generated executable.
*   **Multi-Layer Obfuscation:** Applies multiple layers of obfuscation to the collector's source code before compilation to complicate analysis:
    *   Base16 Encoding.
    *   Compilation to Python bytecode and serialization using the `marshal` module.
    *   Compression of serialized data using the `zlib` library.
    *   Encoding of compressed data using Base32.
    *   An additional layer of custom obfuscation using `openobf.dll` to enhance resistance to reverse engineering.
*   **Build Process Logging:** All stages of the build process, including PyInstaller output, are recorded in `builder_log.txt` for debugging and auditing.

## III. Central Command and Control Server (C2 Server)

The C2 server is a web panel based on FastAPI for receiving, storing, and managing collected data.

### Key Features:

*   **Web Interface:** An intuitive web interface for viewing and managing received logs.
*   **Access Protection:**
    *   **Authentication:** Secure login to the administrative panel using customizable credentials.
    *   **Session IP Binding:** User sessions are bound to their IP address, ensuring logout if an IP address change is detected.
    *   **Bruteforce Protection (Local):** Blocks an IP address for 5 minutes after 5 incorrect login attempts from the same IP address.
    *   **Bruteforce Protection (Global):** In case of 100 global failed login attempts (from different IP addresses), the control panel will be permanently locked until the server is restarted.
    *   **API Documentation Disable:** Access to standard FastAPI documentation (Swagger UI, ReDoc) is completely disabled to enhance security and prevent unauthorized API structure discovery.
*   **Log Management:**
    *   **View Logged Events:** Displays a list of all received logs, including timestamps, IP addresses, computer names, and other meta-information.
    *   **Download Individual Log Files:** Ability to download each individual ZIP archive containing data.
    *   **Mass Log File Download:** A function to download all collected logs in a single ZIP archive.
    *   **Duplicate Deletion:** Upon receiving a new log from an already known "computer name - public IP address" pair, the previous entry and its associated files are automatically deleted and replaced with the new entry.
*   **Uploaded File Handling:**
    *   **Type Filtering:** The data upload endpoint (`/upload`) accepts only ZIP archives, rejecting any other file types.
    *   **Storage Organization:** Each uploaded log is stored in a separate directory on the server.
*   **Server Log Viewing:** Access to the content of the `nohup.out` file (server log) via the web interface for server monitoring.
*   **Debug Console Protection (Client-Side):** Implementation of JavaScript code on the client side to hinder the use of the browser's debug console, including disabling the right-click context menu, detecting F12 and Ctrl+Shift+I/J key presses, as well as an infinite `debugger;` loop and blocking console output.

## IV. Installation and Operation Instructions

### 1. C2 Server Installation and Configuration:

The server can be installed on Linux or Windows systems.

**Prerequisites:**
*   **Recommended Operating System: Ubuntu 20.04.**
*   Python 3.x installed (Python 3.8 or newer is recommended).
*   `pip` utility for installing Python packages.

**Installation Procedure (Linux, Recommended):**
1.  **System Update and Python Installation:** Execute the `Start.sh` script from the server directory. It will automatically update the system, install Python3 and pip3.
    ```bash
    chmod +x Start.sh
    sudo ./Start.sh
    ```
2.  **Server Configuration:** The `Start.sh` script will launch `Config_C2.py`. Follow the command-line instructions:
    *   You will be prompted to enter the desired username and password for C2 administrative panel access.
    *   You will need to specify the port on which the server will listen (e.g., `8000`).
    *   The script will generate a secret key for sessions and save all settings to `config.json`.
    *   After configuration, `Config_C2.py` will offer options to start the server (in foreground debug mode or background mode with `nohup`). Background mode is recommended for production use.

**Installation Procedure (Windows):**
1.  **Dependency Installation:** Ensure you have Python 3.x and `pip` installed. Navigate to the server's root directory (where `requirements.txt` is located) and install the necessary libraries:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Server Configuration:** Run the `Config_C2.py` script:
    ```bash
    python Config_C2.py
    ```
    *   Follow the same instructions as for Linux for entering username, password, and port. `config.json` will be created automatically.
3.  **Server Launch:** After `Config_C2.py` completes, you will be prompted to start the server. Choose the desired launch mode.

**Accessing the Control Panel:**
After successful server launch, the administrative panel can be accessed via a web browser at `http://<YOUR_SERVER_IP>:<PORT>/login`.

### 2. Creating the Collector Module (Stealer) Using the Builder:

**Prerequisites:**
*   Python 3.x installed (Python 3.8+ is recommended).
*   Python packages installed. Navigate to the builder directory and execute:
    ```bash
    pip install PyInstaller colorama Pillow pycryptodome pypiwin32 psutil requests aiofiles pystyle pywin32
    ```
    *(Note: `pypiwin32` might be replaced by `pywin32` depending on Python version and OS).*

**Creation Procedure:**
1.  **Launch Builder:** Run the `BOFAMET2.py` script:
    ```bash
    python BOFAMET2.py
    ```
    Alternatively, if using the compiled builder:
    ```bash
    BOFAMET_C2_builder.exe
    ```
    *   If necessary, the script will request administrator privileges for working with temporary files and PyInstaller.
2.  **Build Configuration:** Follow the interactive instructions:
    *   Enter the IP address of your deployed C2 server (the same one you used during server setup).
    *   Enter the port of your C2 server.
    *   Optionally, provide the full path to an `.ico` file to be used as the icon for the generated executable.
3.  **Build Process:** The builder will automatically obfuscate the collector's source code and compile it into an executable using PyInstaller.
4.  **Result:** The finished executable, named `BOFAMET_BUILD.exe`, will be located in the `dist` directory relative to where the builder was launched.

## V. Collector Obfuscation Principle:

The builder employs a multi-stage approach to obfuscate the collector's source code to ensure its protection:
1.  The raw source code is first encoded using Base16.
2.  The resulting output is compiled into Python bytecode and serialized using the `marshal` module.
3.  The serialized data is then compressed using the `zlib` library.
4.  The compressed data is encoded using Base32.
5.  As a final stage, an additional layer of custom obfuscation is applied, implemented via the `openobf.dll` dynamic-link library.
During the collector's execution, a small loader sequentially decodes and decompresses these layers to execute the original code.

---
**Disclaimer:** This software is provided strictly for educational and research purposes. The developers are not responsible for any misuse of this tool. 
