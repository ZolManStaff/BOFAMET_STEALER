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
    ![C2 Panel Screenshot](path/to/c2_panel_screenshot.png)
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
    ![Login Page Screenshot](path/to/login_page_screenshot.png)

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
    ![Builder Configuration Screenshot](path/to/builder_config_screenshot.png)
3.  **Build Process:** The builder will automatically obfuscate the collector's source code and compile it into an executable using PyInstaller.
4.  **Result:** The finished executable, named `BOFAMET_BUILD.exe`, will be located in the `dist` directory relative to where the builder was launched.
    ![Dist Folder Screenshot](path/to/dist_folder_screenshot.png)

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
