#!/bin/bash

# --- CONFIGURACIÓN VISUAL (ESTILO HACKER) ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# --- COMPROBACIONES INICIALES ---

check_deps() {
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ Error: Necesitas instalar 'jq' para la visualización bonita.${NC}"
        echo -e "Ejecuta: ${YELLOW}sudo apt install jq${NC}"
        exit 1
    fi
    
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${YELLOW}⚠️  Ejecuta este script con SUDO para gestionar Tor.${NC}"
        exit 1
    fi
}

start_tor() {
    echo -e "${BLUE}➤ Iniciando servicio Tor...${NC}"
    systemctl start tor
    sleep 2
    if systemctl is-active --quiet tor; then
        echo -e "${GREEN}✅ Tor está ACTIVO.${NC}"
    else
        echo -e "${RED}❌ Error al iniciar Tor.${NC}"
    fi
}

stop_tor() {
    echo -e "${RED}➤ Deteniendo servicio Tor...${NC}"
    systemctl stop tor
    echo -e "${GREEN}💀 Servicio Tor eliminado.${NC}"
}

check_ip() {
    echo -e "${CYAN}➤ Rastreando identidad vía Proxychains...${NC}"
    
    # Capturamos el JSON en una variable (silenciando el output de proxychains)
    # Usamos ip-api porque da muchos datos gratis y suele tolerar Tor
    JSON_DATA=$(proxychains -q curl -s --connect-timeout 10 "http://ip-api.com/json/")
    
    # Comprobamos si la petición falló (vacío)
    if [ -z "$JSON_DATA" ]; then
        echo -e "${RED}❌ Fallo de conexión. ¿Tor está encendido? ¿Timeout?${NC}"
        return
    fi

    # Extraemos datos con JQ (limpio y seguro)
    IP=$(echo "$JSON_DATA" | jq -r '.query')
    COUNTRY=$(echo "$JSON_DATA" | jq -r '.country')
    CITY=$(echo "$JSON_DATA" | jq -r '.city')
    ISP=$(echo "$JSON_DATA" | jq -r '.isp')
    ORG=$(echo "$JSON_DATA" | jq -r '.org')
    REGION=$(echo "$JSON_DATA" | jq -r '.regionName')
    
    # Si ip-api falla al detectar, jq devuelve null. Lo controlamos.
    if [ "$IP" == "null" ]; then
         echo -e "${RED}❌ La API no devolvió datos válidos.${NC}"
         return
    fi

    # --- LA TABLA MOLONA ---
    echo -e ""
    echo -e "${WHITE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${WHITE}║           🕵️  IDENTITY CARD (TOR)         ║${NC}"
    echo -e "${WHITE}╠════════════════════════════════════════════╣${NC}"
    printf "${WHITE}║${CYAN} %-12s ${WHITE}│${GREEN} %-27s ${WHITE}║\n${NC}" "IP Address" "$IP"
    echo -e "${WHITE}╟────────────────────────────────────────────╢${NC}"
    printf "${WHITE}║${CYAN} %-12s ${WHITE}│${YELLOW} %-27s ${WHITE}║\n${NC}" "Country" "$COUNTRY"
    printf "${WHITE}║${CYAN} %-12s ${WHITE}│${YELLOW} %-27s ${WHITE}║\n${NC}" "Region" "$REGION"
    printf "${WHITE}║${CYAN} %-12s ${WHITE}│${YELLOW} %-27s ${WHITE}║\n${NC}" "City" "$CITY"
    echo -e "${WHITE}╟────────────────────────────────────────────╢${NC}"
    # Cortamos el ISP si es muy largo para que no rompa la tabla (cut -c)
    SHORT_ISP=$(echo "$ISP" | cut -c 1-27)
    printf "${WHITE}║${CYAN} %-12s ${WHITE}│${BLUE} %-27s ${WHITE}║\n${NC}" "ISP" "$SHORT_ISP"
    echo -e "${WHITE}╚════════════════════════════════════════════╝${NC}"
    echo -e ""
}

rotate_ip() {
    echo -e "${YELLOW}➤ Solicitando nueva identidad (Signal HUP)...${NC}"
    killall -HUP tor
    echo -e "${GREEN}✅ Señal enviada.${NC}"
    echo -ne "Estableciendo nuevo circuito"
    
    for i in {1..5}; do
        echo -ne "."
        sleep 1
    done
    echo -e " ${GREEN}Listo.${NC}"
}

# --- MENÚ PRINCIPAL ---

check_deps

while true; do
    echo -e "\n${BLUE}╔════════ GHOST MODE v2.0 ════════╗${NC}"
    echo -e "${BLUE}║${NC} 1. 🔥 Iniciar Tor               ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC} 2. 🕵️  Ver Identidad (Tabla)     ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC} 3. 🔄 Rotar IP                  ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC} 4. 💀 Matar Tor                 ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC} 5. 🚪 Salir                     ${BLUE}║${NC}"
    echo -e "${BLUE}╚═════════════════════════════════╝${NC}"
    read -p "Opción > " op

    case $op in
        1) start_tor ;;
        2) check_ip ;;
        3) rotate_ip; check_ip ;; # Rotar y mostrar la tabla del tirón
        4) stop_tor ;;
        5) echo "Cerrando..."; exit ;;
        *) echo -e "${RED}Opción no válida.${NC}" ;;
    esac
    
    echo -e "Pulsa ENTER para continuar..."
    read
done