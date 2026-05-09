#!/usr/bin/env bash
set -u

VM_NAME="${KALI_VM_NAME:-kali-lab}"
SSH_HOST="${KALI_SSH_HOST:-kali-lab}"

echo "[+] VirtualBox VM: ${VM_NAME}"
if ! command -v VBoxManage >/dev/null 2>&1; then
  echo "[!] VBoxManage no está disponible en PATH."
  exit 1
fi

if VBoxManage list vms | grep -q "\"${VM_NAME}\""; then
  echo "[OK] VM registrada: ${VM_NAME}"
else
  echo "[!] VM no registrada: ${VM_NAME}"
  exit 2
fi

if VBoxManage list runningvms | grep -q "\"${VM_NAME}\""; then
  echo "[OK] VM en ejecución"
else
  echo "[INFO] VM apagada"
fi

echo "[+] Red/NAT/SSH forwarding:"
VBoxManage showvminfo "${VM_NAME}" --machinereadable | grep -E '^(VMState=|nic1=|Forwarding)' || true

echo "[+] Comprobación SSH no interactiva (${SSH_HOST})"
if ssh -o BatchMode=yes -o ConnectTimeout=5 "${SSH_HOST}" 'echo SSH_OK && hostname' 2>/dev/null; then
  echo "[OK] SSH disponible"
else
  echo "[INFO] SSH no confirmado"
fi
