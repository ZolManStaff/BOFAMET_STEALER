![LOGO Screenshot](https://raw.githubusercontent.com/ZolManStaff/BOFAMET_STEALER/refs/heads/main/Gallery/photo_2025-06-22_19-48-33.jpg)

---
**UPD: 18.07.25**

# BOFAMET – Stealer

BOFAMET is a comprehensive solution for collecting data from target systems, consisting of a collector module (stealer) and a centralized command and control (C2) server. The collector, written in **GoLang**, is compiled into a standalone Windows executable, and the collected data is transmitted to the C2 server, developed using FastAPI. The collector also features a dedicated builder with a modern Electron-based graphical interface for easy customization.

## I. Data Collector Module (Stealer)

The collector module is designed for comprehensive information gathering from a compromised system, now leveraging the power and stealth of GoLang.

### Key Features:

*   **Browser Data Extraction:**
    *   Retrieves saved login credentials (usernames, passwords) from a wide range of web browsers (Chrome, Edge, Opera, Yandex, Brave, Vivaldi, Slimjet, Iridium, CentBrowser).
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
*   **Discord Token Discovery:** Scans the system for Discord authentication tokens in various locations and records them.
*   **Steam Configuration:** Copies configuration files of the Steam client.
*   **Epic Games Configuration:** Copies configuration files of the Epic client.
*   **Targeted File Exfiltration:** Searches for and steals files with specific extensions (.doc, .docx, .xls, .xlsx, .ppt, .pptx, .pdf, .bmp) from user directories.
*   **Crypto Wallet Extraction:** Identifies and copies files associated with cryptocurrency wallets (e.g., `wallet.dat`, `key.json`, `keystore`, `mnemonic.txt`, `seed.txt`, as well as SSH keys like `id_rsa`).
*   **Data Transmission:** Archives all collected data into ZIP files and subsequently transmits them, along with system information and geolocation data, to the configured C2 server.

## II. Collector Builder Module (BOFAMET BUILDER)

The builder is now an Electron-based desktop application designed to create a customizable executable file for the GoLang collector.

### Key Features:

*   **Modern GUI:** User-friendly graphical interface built with Electron, HTML, CSS, and JavaScript.
*   **C2 Server Configuration:** Interactive setting of the IP address and port of the central control server to which collected data will be sent.
*   **Output File Customization:**
    *   Ability to specify the desired name for the compiled malware executable.
    *   Ability to choose the output directory for the compiled `.exe` file.
*   **EXE Compilation (GoLang):**
    *   Compiles the GoLang collector into a single, self-contained Windows executable (`.exe`).
    *   Includes the `-H=windowsgui` flag to ensure the compiled malware runs without a visible console window.
*   **Icon Customization:** Ability to add a custom icon file (`.ico`) to the generated executable, utilizing the `rsrc` tool.
*   **UPX Compression (Optional):** Option to apply UPX compression to the final executable, reducing its size and potentially hindering basic analysis.
*   **Integrated Malware Source:** The GoLang malware source code is bundled directly within the Electron builder's compiled `.exe`, ensuring self-sufficiency and ease of distribution.
*   **Build Process Logging:** All stages of the build process, including Go compiler and UPX output, are displayed in the Electron application's developer console for debugging.

## III. Central Command and Control Server (C2 Server)

The C2 server is a web panel based on FastAPI for receiving, storing, and managing collected data.

### Key Features:

*   **Web Interface:** An intuitive web interface for viewing and managing received logs.
    ![C2 Panel Screenshot](https://raw.githubusercontent.com/ZolManStaff/BOFAMET_STEALER/refs/heads/main/Gallery/Скриншот%2018-07-2025%20202742.jpg)
    ![C2 Panel Screenshot](https://raw.githubusercontent.com/ZolManStaff/BOFAMET_STEALER/refs/heads/main/Gallery/Скриншот%2018-07-2025%20210340.jpg)
    ![C2 Panel Screenshot](https://raw.githubusercontent.com/ZolManStaff/BOFAMET_STEALER/refs/heads/main/Gallery/Скриншот%2018-07-2025%20202849.jpg)
*   **Access Protection:**
    *   **Authentication:** Secure login to the administrative panel using customizable credentials.
    *   **Session IP Binding:** User sessions are bound to their IP address, ensuring logout if an IP address change is detected.
    *   **Bruteforce Protection (Local):** Blocks an IP address for 5 minutes after 5 incorrect login attempts from the same IP address.
    *   **Bruteforce Protection (Global):** In case of 100 global failed login attempts (from different IP addresses), the control panel will be permanently locked until the server is restarted.
    *   **API Documentation Disable:** Access to standard FastAPI documentation (Swagger UI, ReDoc) is completely disabled to enhance security and prevent unauthorized API structure discovery.
*   **Log Management:**
    *   **View Logged Events:** Displays a list of all received logs, including timestamps, IP addresses, computer names, and other meta-information.
    *   **Log Count Display:** Shows the total number of collected logs directly in the interface.
    *   **Download Individual Log Files:** Ability to download each individual ZIP archive containing data.
    *   **Mass Log File Download:** A function to download all collected logs in a single ZIP archive.
    *   **Delete Individual Logs:** Provides a button to delete specific log entries and their associated files.
    *   **Duplicate Deletion:** Upon receiving a new log from an already known "computer name - public IP address" pair, the previous entry and its associated files are automatically deleted and replaced with the new entry.
*   **Telegram Notifications:**
    *   **Configurable Settings:** Dedicated panel in the web interface to configure Telegram bot token, chat ID, and enable/disable notifications.
    *   **Automated Alerts:** Sends automatic notifications to a Telegram chat upon receipt of a new log from a compromised system.
*   **Server Status Display:** Shows the server's public IP address, listening port, and ping directly in the control panel header for quick monitoring.
*   **Uploaded File Handling:**
    *   **Type Filtering:** The data upload endpoint (`/upload`) accepts only ZIP archives, rejecting any other file types.
    *   **Storage Organization:** Each uploaded log is stored in a separate directory on the server.
*   **Server Log Viewing:** Access to the content of the `nohup.out` file (server log) via the web interface for server monitoring.
*   **Debug Console Protection (Client-Side):** Implementation of JavaScript code on the client side to hinder the use of the browser's debug console, including disabling the right-click context menu, detecting F12 and Ctrl+Shift+I/J key presses, as well as an infinite `debugger;` loop and blocking console output.

## IV. Installation and Operation Instructions

### 1. C2 Server Installation and Configuration:

The server can be installed on Linux system.

**Prerequisites:**
*   **Recommended Operating System: Ubuntu 20.04.**
*   Python 3.8+ installed.
*   `pip` utility for installing Python packages.

**Installation Procedure (Linux, Recommended):**
1.  **System Update and Python Installation:** Execute the `Start.sh` script from the server directory (`JSbuilder/BOFAMET_SERVER`). It will automatically update the system, install Python3 and pip3.
    ```bash
    chmod +x Start.sh
    sudo ./Start.sh
    ```
2.  **Server Configuration:** The `Start.sh` script will launch `Config_C2.py`. Follow the command-line instructions:
    *   You will be prompted to enter the desired username and password for C2 administrative panel access.
    *   You will need to specify the port on which the server will listen (e.g., `8000`).
    *   The script will generate a secret key for sessions and save initial settings to `config.json`.
    *   After configuration, `Config_C2.py` will offer options to start the server (in foreground debug mode or background mode with `nohup`). Background mode is recommended for production use.
    *   **Telegram Bot settings and Server IP are now configured/updated directly via the web panel after initial login.**

**Accessing the Control Panel:**
After successful server launch, the administrative panel can be accessed via a web browser at `http://<YOUR_SERVER_IP>:<PORT>/login`.
    ![Login Page Screenshot](https://raw.githubusercontent.com/ZolManStaff/BOFAMET_STEALER/refs/heads/main/Gallery/%D0%A1%D0%BA%D1%80%D0%B8%D0%BD%D1%88%D0%BE%D1%82%2018-06-2025%20081208.jpg)

### 2. Creating the Collector Module (Stealer) Using the BOFAMET BUILDER:

**Prerequisites:**
*   **GoLang:** Install GoLang (version 1.18 or higher recommended).
*   **Node.js & npm:** Install Node.js, which includes npm (Node Package Manager).
*   **rsrc:** Install `rsrc` for embedding icons into Go executables:
    ```powershell
    go install github.com/akavel/rsrc@latest
    ```
*   **UPX:** Download `upx.exe` from the official UPX GitHub releases and place it directly into the `JSbuilder` directory.

**Building the Electron Builder (Recommended for Distribution):**
*(Skip this step if you are using a pre-built release version of BOFAMET Builder.)*
1.  **Navigate to the `JSbuilder` directory** in your terminal.
    ```bash
    cd JSbuilder
    ```
2.  **Install Electron dependencies:**
    ```bash
    npm install
    ```
3.  **Install electron-packager:**
    ```bash
    npm install electron-packager --save-dev
    ```
4.  **Build the BOFAMET BUILDER `.exe`:**
    ```bash
    npm run package-win
    ```
    The compiled builder will be located in the `JSbuilder/releases/bofamet-builder-win32-x64` directory. You can then distribute this `BOFAMET Builder.exe` to easily create malware payloads.

**Using the BOFAMET BUILDER (Electron App):**
1.  **Launch the builder:**
    *   If you built the `.exe` of the builder: Run `BOFAMET Builder.exe` from the `releases` directory.
    *   If you want to run directly from source (for development): Navigate to the `JSbuilder` directory and run `npm start`.
    ![Builder Configuration Screenshot](https://raw.githubusercontent.com/ZolManStaff/BOFAMET_STEALER/refs/heads/main/Gallery/Скриншот%2018-07-2025%20210627.jpg)
2.  **Build Configuration:** In the BOFAMET BUILDER interface:
    *   Enter the C2 Server URL (e.g., `http://your-server-ip:8000`).
    *   Enter the desired Output File Name (e.g., `payload`).
    *   Choose the Output Directory where the compiled malware will be saved.
    *   (Optional) Select an Icon File (`.ico`).
    *   (Optional) Check the "Use UPX Compression" box.
3.  **Build Process:** Click the "Build" button. The builder will:
    *   Extract the GoLang malware source and UPX executable to a temporary location.
    *   Compile the GoLang code into an `.exe` file.
    *   Apply the custom icon (if provided).
    *   Apply UPX compression (if selected).
    *   Save the final malware executable to your chosen output directory.
4.  **Result:** The finished executable (e.g., `payload.exe`) will be located in the output directory you selected.

## V. Collector Compilation and Obfuscation Principle:

The BOFAMET builder now compiles the collector module written in GoLang, employing the following principles for stealth and efficiency:
1.  **Native Compilation:** GoLang code is compiled directly into a single, self-contained native executable (`.exe`). This means no external runtimes (like Python interpreters) are needed on the target system, resulting in smaller, faster, and more portable binaries.
2.  **Hidden Console:** The Go compiler is instructed to build the executable as a Windows GUI application (`-ldflags "-H=windowsgui"`), ensuring that no console window appears when the malware is executed.
3.  **Icon Embedding:** The `rsrc` tool is used to embed a custom icon directly into the `.exe` file, making the payload visually customizable.
4.  **UPX Compression (Optional):** If selected, the generated `.exe` is further compressed using UPX. This reduces the file size, which can aid in delivery, and adds a layer of packing that may slightly complicate static analysis by some antivirus solutions.

During execution, the native Go executable performs its tasks directly, without intermediate decryption or loading steps typical of interpreted languages.

---
**Disclaimer:** This software is provided strictly for educational and research purposes. The developers are not responsible for any misuse of this tool.

---

**ОБНОВЛЕНИЕ: 18.07.25**

# BOFAMET – Стилер

BOFAMET – это комплексное решение для сбора данных с целевых систем, состоящее из модуля-сборщика (стилера) и централизованного сервера управления (C2). Модуль-сборщик, написанный на **GoLang**, компилируется в автономный исполняемый файл для Windows, а собранные данные передаются на C2-сервер, разработанный с использованием FastAPI. Сборщик также включает в себя специальный билдер с современным графическим интерфейсом на базе Electron для легкой настройки.

## I. Модуль Сбора Данных (Стилер)

Модуль-сборщик предназначен для всестороннего сбора информации с скомпрометированной системы, теперь использующий мощь и скрытность GoLang.

### Ключевые Возможности:

*   **Извлечение Данных Браузеров:**
    *   Получает сохраненные учетные данные (логины, пароли) из широкого спектра веб-браузеров (Chrome, Edge, Opera, Yandex, Brave, Vivaldi, Slimjet, Iridium, CentBrowser).
    *   Собирает файлы cookie браузеров для потенциального обхода аутентификации.
    *   Извлекает историю просмотров и данные автозаполнения форм из поддерживаемых браузеров.
*   **Сбор Системной Информации:** Детальный сбор информации о хост-системе, включая:
    *   Операционную систему (тип, версия).
    *   Аппаратное обеспечение (процессор, количество ядер, ОЗУ, информация о дисковом пространстве).
    *   Сетевую конфигурацию (локальный IP-адрес, MAC-адрес, данные Wi-Fi SSID и BSSID).
    *   Информацию о пользователе (имя пользователя, имя компьютера).
    *   Идентификацию публичного IP-адреса и данные геолокации (город, регион, страна, широта, долгота).
*   **Скриншот Рабочего Стола:** Захватывает изображение текущего рабочего стола целевой системы.
*   **Извлечение Сессий Telegram:** Пытается получить локальные файлы сессий Telegram (путем принудительного завершения процесса Telegram для получения доступа к файлам сессий).
*   **Обнаружение Токенов Discord:** Сканирует систему на наличие токенов аутентификации Discord в различных местах и записывает их.
*   **Конфигурация Steam:** Копирует файлы конфигурации клиента Steam.
*   **Конфигурация Epic Games:** Копирует файлы конфигурации клиента Epic Games.
*   **Целевая Эксфильтрация Файлов:** Ищет и крадет файлы с определенными расширениями (.doc, .docx, .xls, .xlsx, .ppt, .pptx, .pdf, .bmp) из пользовательских директорий.
*   **Извлечение Криптокошельков:** Идентифицирует и копирует файлы, связанные с криптовалютными кошельками (например, `wallet.dat`, `key.json`, `keystore`, `mnemonic.txt`, `seed.txt`, а также SSH-ключи, такие как `id_rsa`).
*   **Передача Данных:** Архивирует все собранные данные в ZIP-файлы и впоследствии передает их вместе с системной информацией и данными геолокации на настроенный C2-сервер.

## II. Модуль-Билдер Сборщика (BOFAMET BUILDER)

Билдер теперь представляет собой десктопное приложение на базе Electron, предназначенное для создания настраиваемого исполняемого файла для сборщика на GoLang.

### Ключевые Возможности:

*   **Современный GUI:** Удобный графический интерфейс, построенный с использованием Electron, HTML, CSS и JavaScript.
*   **Конфигурация C2-Сервера:** Интерактивная настройка IP-адреса и порта центрального сервера управления, на который будут отправляться собранные данные.
*   **Настройка Выходного Файла:**
    *   Возможность указать желаемое имя для скомпилированного исполняемого файла малвари.
    *   Возможность выбора выходной директории для скомпилированного файла `.exe`.
*   **Компиляция EXE (GoLang):**
    *   Компилирует сборщик на GoLang в один автономный нативный исполняемый файл для Windows (`.exe`).
    *   Включает флаг `-H=windowsgui`, чтобы гарантировать запуск скомпилированной малвари без видимого окна консоли.
*   **Настройка Иконки:** Возможность добавить пользовательский файл иконки (`.ico`) к генерируемому исполняемому файлу, используя инструмент `rsrc`.
*   **UPX-Сжатие (Опционально):** Опция применения UPX-сжатия к финальному исполняемому файлу, уменьшая его размер и потенциально затрудняя базовый анализ.
*   **Интегрированный Исходник Малвари:** Исходный код малвари на GoLang упаковывается непосредственно внутри скомпилированного `.exe` билдера Electron, обеспечивая самодостаточность и легкость распространения.
*   **Логирование Процесса Сборки:** Все этапы процесса сборки, включая вывод компилятора Go и UPX, отображаются в консоли разработчика приложения Electron для отладки.

## III. Центральный Сервер Управления (C2-Сервер)

C2-сервер представляет собой веб-панель на базе FastAPI для приема, хранения и управления собранными данными.

### Ключевые Возможности:

*   **Веб-Интерфейс:** Интуитивно понятный веб-интерфейс для просмотра и управления полученными логами.
*   **Защита Доступа:**
    *   **Аутентификация:** Безопасный вход в административную панель с использованием настраиваемых учетных данных.
    *   **Привязка Сессии к IP:** Сессии пользователей привязываются к их IP-адресу, обеспечивая выход из системы при обнаружении изменения IP-адреса.
    *   **Защита от Брутфорса (Локальная):** Блокирует IP-адрес на 5 минут после 5 некорректных попыток входа с одного и того же IP-адреса.
    *   **Защита от Брутфорса (Глобальная):** В случае 100 глобальных неудачных попыток входа (с разных IP-адресов) панель управления будет заблокирована навсегда до перезапуска сервера.
    *   **Отключение Документации API:** Доступ к стандартной документации FastAPI (Swagger UI, ReDoc) полностью отключен для повышения безопасности и предотвращения несанкционированного обнаружения структуры API.
*   **Управление Логами:**
    *   **Просмотр Зарегистрированных Событий:** Отображает список всех полученных логов, включая временные метки, IP-адреса, имена компьютеров и другую метаинформацию.
    *   **Отображение Количества Лог-Файлов:** Показывает общее количество собранных логов непосредственно в интерфейсе.
    *   **Загрузка Отдельных Лог-Файлов:** Возможность загрузки каждого отдельного ZIP-архива, содержащего данные.
    *   **Массовая Загрузка Лог-Файлов:** Функция для загрузки всех собранных логов в одном ZIP-архиве.
    *   **Удаление Отдельных Лог-Файлов:** Предоставляет кнопку для удаления определенных записей логов и связанных с ними файлов.
    *   **Удаление Дубликатов:** При получении нового лога от уже известной пары "имя компьютера - публичный IP-адрес" предыдущая запись и связанные с ней файлы автоматически удаляются и заменяются новой записью.
*   **Уведомления Telegram:**
    *   **Настраиваемые Параметры:** Выделенная панель в веб-интерфейсе для настройки токена Telegram-бота, ID чата и включения/отключения уведомлений.
    *   **Автоматические Оповещения:** Отправляет автоматические уведомления в чат Telegram при получении нового лога со скомпрометированной системы.
*   **Отображение Статуса Сервера:** Показывает публичный IP-адрес сервера, прослушиваемый порт и пинг непосредственно в заголовке панели управления для быстрого мониторинга.
*   **Обработка Загруженных Файлов:**
    *   **Фильтрация по Типу:** Эндпоинт загрузки данных (`/upload`) принимает только ZIP-архивы, отклоняя любые другие типы файлов.
    *   **Организация Хранения:** Каждый загруженный лог хранится в отдельной директории на сервере.
*   **Просмотр Логов Сервера:** Доступ к содержимому файла `nohup.out` (лог сервера) через веб-интерфейс для мониторинга сервера.
*   **Защита Консоли Разработчика (На Стороне Клиента):** Реализация JavaScript-кода на стороне клиента для затруднения использования консоли отладки браузера, включая отключение контекстного меню по правому клику, обнаружение нажатий клавиш F12 и Ctrl+Shift+I/J, а также бесконечный цикл `debugger;` и блокировку вывода в консоль.

## IV. Инструкции по Установке и Эксплуатации

### 1. Установка и Настройка C2-Сервера:

Сервер может быть установлен на системе Linux.

**Предварительные Условия:**
*   **Рекомендуемая Операционная Система: Ubuntu 20.04.**
*   Установлен Python 3.8+ .
*   Утилита `pip` для установки пакетов Python.

**Процедура Установки (Linux, Рекомендуется):**
1.  **Обновление Системы и Установка Python:** Выполните скрипт `Start.sh` из директории сервера (`JSbuilder/BOFAMET_SERVER`). Он автоматически обновит систему, установит Python3 и pip3.
    ```bash
    chmod +x Start.sh
    sudo ./Start.sh
    ```
2.  **Конфигурация Сервера:** Скрипт `Start.sh` запустит `Config_C2.py`. Следуйте инструкциям командной строки:
    *   Вам будет предложено ввести желаемое имя пользователя и пароль для доступа к административной панели C2.
    *   Вам нужно будет указать порт, на котором будет прослушивать сервер (например, `8000`).
    *   Скрипт сгенерирует секретный ключ для сессий и сохранит начальные настройки в `config.json`.
    *   После настройки `Config_C2.py` предложит варианты запуска сервера (в режиме отладки на переднем плане или в фоновом режиме с `nohup`). Фоновый режим рекомендуется для производственного использования.
    *   **Настройки Telegram-бота и IP-адрес сервера теперь настраиваются/обновляются непосредственно через веб-панель после первого входа.**

**Доступ к Панели Управления:**
После успешного запуска сервера административная панель будет доступна через веб-браузер по адресу `http://<ВАШ_IP_СЕРВЕРА>:<ПОРТ>/login`.

### 2. Создание Модуля-Сборщика (Стилера) с помощью BOFAMET BUILDER:

**Предварительные Условия:**
*   **GoLang:** Установите GoLang (рекомендуется версия 1.18 или выше).
*   **Node.js & npm:** Установите Node.js, который включает npm (Node Package Manager).
*   **rsrc:** Установите `rsrc` для встраивания иконок в исполняемые файлы Go:
    ```powershell
    go install github.com/akavel/rsrc@latest
    ```
*   **UPX:** Загрузите `upx.exe` с официальных релизов UPX на GitHub и поместите его непосредственно в директорию `JSbuilder`.

**Сборка Electron-Билдера (Рекомендуется для Распространения):**
*(Пропустите этот шаг, если вы используете уже собранную версию BOFAMET Builder.)*
1.  **Перейдите в директорию `JSbuilder`** в вашем терминале.
    ```bash
    cd JSbuilder
    ```
2.  **Установите зависимости Electron:**
    ```bash
    npm install
    ```
3.  **Установите electron-packager:**
    ```bash
    npm install electron-packager --save-dev
    ```
4.  **Соберите `.exe` файл BOFAMET BUILDER:**
    ```bash
    npm run package-win
    ```
    Скомпилированный билдер будет расположен в директории `JSbuilder/releases/bofamet-builder-win32-x64`. Затем вы можете распространять этот `BOFAMET Builder.exe` для легкого создания полезных нагрузок малвари.

**Использование BOFAMET BUILDER (Приложение Electron):**
1.  **Запустите билдер:**
    *   Если вы собрали `.exe` билдера: Запустите `BOFAMET Builder.exe` из директории `releases`.
    *   Если вы хотите запустить напрямую из исходников (для разработки): Перейдите в директорию `JSbuilder` и запустите `npm start`.
2.  **Конфигурация Сборки:** В интерфейсе BOFAMET BUILDER:
    *   Введите URL C2-сервера (например, `http://ваш-сервер-ip:8000`).
    *   Введите желаемое Имя Выходного Файла (например, `payload`).
    *   Выберите Выходную Директорию, куда будет сохранен скомпилированный файл малвари.
    *   (Опционально) Выберите Файл Иконки (`.ico`).
    *   (Опционально) Отметьте флажок "Использовать UPX-сжатие".
3.  **Процесс Сборки:** Нажмите кнопку "Собрать". Билдер выполнит:
    *   Извлечет исходный код малвари GoLang и исполняемый файл UPX во временное расположение.
    *   Скомпилирует код GoLang в файл `.exe`.
    *   Применит пользовательскую иконку (если предоставлена).
    *   Применит UPX-сжатие (если выбрано).
    *   Сохранит окончательный исполняемый файл малвари в выбранную вами выходную директорию.
4.  **Результат:** Готовый исполняемый файл (например, `payload.exe`) будет расположен в выбранной вами выходной директории.

## V. Принцип Компиляции и Обфускации Сборщика:

Билдер BOFAMET теперь компилирует модуль-сборщик, написанный на GoLang, используя следующие принципы скрытности и эффективности:
1.  **Нативная Компиляция:** Код GoLang компилируется непосредственно в один автономный нативный исполняемый файл (`.exe`). Это означает, что на целевой системе не требуются внешние среды выполнения (например, интерпретаторы Python), что приводит к созданию меньших, более быстрых и более переносимых бинарных файлов.
2.  **Скрытая Консоль:** Компилятор Go инструктируется собирать исполняемый файл как оконное приложение Windows GUI (`-ldflags "-H=windowsgui"`), гарантируя, что при запуске малвари не появится окно консоли.
3.  **Встраивание Иконки:** Инструмент `rsrc` используется для встраивания пользовательской иконки непосредственно в файл `.exe`, что делает полезную нагрузку визуально настраиваемой.
4.  **UPX-Сжатие (Опционально):** При выборе этой опции сгенерированный `.exe` дополнительно сжимается с помощью UPX. Это уменьшает размер файла, что может помочь в доставке, и добавляет слой упаковки, который может немного усложнить статический анализ некоторыми антивирусными решениями.

Во время выполнения нативный исполняемый файл Go выполняет свои задачи напрямую, без промежуточных шагов дешифрования или загрузки, характерных для интерпретируемых языков.

---
**Отказ от ответственности:** Это программное обеспечение предоставляется исключительно в образовательных и исследовательских целях. Разработчики не несут ответственности за любое неправомерное использование этого инструмента.
