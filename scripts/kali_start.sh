#!/usr/bin/env bash
set -u

VM_NAME="${KALI_VM_NAME:-kali-lab}"
MODE="${KALI_START_MODE:-headless}"

if ! command -v VBoxManage >/dev/null 2>&1; then
  echo "[!] VBoxManage no está disponible."
  exit 1
fi

if ! VBoxManage list vms | grep -q "\"${VM_NAME}\""; then
  echo "[!] No existe VM registrada: ${VM_NAME}"
  exit 2
fi

if VBoxManage list runningvms | grep -q "\"${VM_NAME}\""; then
  echo "[OK] ${VM_NAME} ya está en ejecución."
  exit 0
fi

echo "[+] Iniciando ${VM_NAME} en modo ${MODE}..."
VBoxManage startvm "${VM_NAME}" --type "${MODE}"
echo "[OK] Orden de arranque enviada."
