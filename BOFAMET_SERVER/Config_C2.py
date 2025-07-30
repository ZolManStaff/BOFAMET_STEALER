import os
import json
import sys
import subprocess
import datetime

if sys.version_info.major >= 3:
    try:
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f"BOFAMET: Changed current working directory to: {os.getcwd()}")

CONFIG_FILE = 'config.json'

VALID_USERNAME = None
VALID_PASSWORD = None
LISTEN_PORT = None
GLOBAL_SECRET_KEY = None

def load_config():

    global VALID_USERNAME, VALID_PASSWORD, LISTEN_PORT, GLOBAL_SECRET_KEY

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                VALID_USERNAME = config_data.get('username')
                VALID_PASSWORD = config_data.get('password')
                LISTEN_PORT = config_data.get('port')
                GLOBAL_SECRET_KEY = bytes.fromhex(config_data.get('secret_key'))
                print("Configuration loaded from config.json.")
                return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading configuration from {CONFIG_FILE}: {e}. Running setup CLI.")
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            return False
    return False

def setup_cli():

    global VALID_USERNAME, VALID_PASSWORD, LISTEN_PORT, GLOBAL_SECRET_KEY

    print("""
██████   ██████  ███████  █████  ███    ███ ███████ ████████      ██████ ██████  
██   ██ ██    ██ ██      ██   ██ ████  ████ ██         ██        ██           ██ 
██████  ██    ██ █████   ███████ ██ ████ ██ █████      ██        ██       █████  
██   ██ ██    ██ ██      ██   ██ ██  ██  ██ ██         ██        ██      ██      
██████   ██████  ██      ██   ██ ██      ██ ███████    ██         ██████ ███████ 
                                                                                                                                                                
""")
    print("\n--- Initial Server Setup ---")
    print("This appears to be the first run or configuration is missing.")
    print("Please set up the admin panel credentials and listening port.")

    username = input("Enter desired admin username: ").strip()
    password = input("Enter desired admin password: ").strip()
    
    while True:
        try:
            port = int(input("Enter desired listening port (e.g., 8000): ").strip())
            if not (1024 <= port <= 65535):
                print("Invalid port. Please choose a port between 1024 and 65535.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a numeric value for the port.")
    
    secret_key_bytes = os.urandom(32)
    secret_key_hex = secret_key_bytes.hex()

    config_data = {
        'username': username,
        'password': password,
        'port': port,
        'secret_key': secret_key_hex
    }

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)
    print(f"Configuration saved to {CONFIG_FILE}.")

    VALID_USERNAME = username
    VALID_PASSWORD = password
    LISTEN_PORT = port
    GLOBAL_SECRET_KEY = secret_key_bytes

if __name__ == '__main__':
    config_exists = os.path.exists(CONFIG_FILE)
    config_loaded_successfully = False

    if config_exists:
        print(f"\n--- Configuration File '{CONFIG_FILE}' Found ---")
        print("Do you want to:")
        print("1. Load existing configuration (recommended)")
        print("2. Set up a new configuration (will overwrite existing)")
        
        while True:
            choice_config = input("Enter your choice (1 or 2): ").strip()
            if choice_config == '1':
                config_loaded_successfully = load_config()
                if not config_loaded_successfully:
                    print("BOFAMET: Existing configuration is corrupted. Running setup CLI to create a new one.")
                    setup_cli()
                break
            elif choice_config == '2':
                print("SatanGPT: Proceeding with new configuration setup. Existing config will be overwritten!")
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)
                setup_cli()
                config_loaded_successfully = True
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")
    else:
        print("BOFAMET: Configuration file not found. Running initial setup CLI.")
        setup_cli()
        config_loaded_successfully = True

    if not config_loaded_successfully:
        print("BOFAMET: Failed to load or set up configuration. Exiting!")
        sys.exit(1)
    
    while True:
        print("\n--- Server Launch Options ---")
        print("How do you want to run the server?")
        print("1. Run server in debug mode (foreground)")
        print("2. Run server in background (with nohup, recommended for production)")
        print("3. Set up a new configuration (username, password, port)")

        choice = input("Enter your choice (1, 2, or 3): ").strip()
        if choice == '1':
            print(f"Starting server in debug mode on http://0.0.0.0:{LISTEN_PORT}...")
            print("Enter your server's IP address and listening port in the following format: IP:PORT")
            print("It may take some time to start the server for the first time, but don't worry!")
            os.execv(sys.executable, [sys.executable, 'server.py'])
            break 
        elif choice == '2':
            print(f"Starting server in background using nohup on http://0.0.0.0:{LISTEN_PORT}...")
            try:
                command = f"nohup uvicorn server:app --host 0.0.0.0 --port {LISTEN_PORT} &"
                subprocess.Popen(command, shell=True) 

                print("Server process initiated in background. Check 'nohup.out' for logs.")
                print("Enter your server's IP address and listening port in the following format: IP:PORT")
                print("It may take some time to start the server for the first time, but don't worry!")
                sys.exit(0)
            except Exception as e:
                print(f"Error launching server in background: {e}. Try running manually.")
            break
        elif choice == '3':
            print("BOFAMET: Reconfiguring the server. Prepare for new settings!")
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            setup_cli()
        else:
            print("Invalid choice. Please enter 1, 2, or 3.") 
