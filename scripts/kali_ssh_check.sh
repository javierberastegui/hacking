#!/usr/bin/env bash
set -u

SSH_TARGET="${1:-kali-lab}"

echo "[+] Probando SSH: ${SSH_TARGET}"
ssh -o BatchMode=yes \
    -o ConnectTimeout=5 \
    -o StrictHostKeyChecking=accept-new \
    "${SSH_TARGET}" 'echo SSH_OK && hostname && whoami'
