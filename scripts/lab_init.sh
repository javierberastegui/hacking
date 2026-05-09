#!/usr/bin/env bash
set -euo pipefail

LAB_NAME="${1:-}"
BASE_DIR="${LAB_BASE_DIR:-./labs}"
TEMPLATE_DIR="${TEMPLATE_DIR:-./templates}"

if [[ -z "${LAB_NAME}" ]]; then
  echo "Uso: $0 <nombre-lab>"
  exit 1
fi

SAFE_NAME="$(printf '%s' "${LAB_NAME}" | tr ' ' '-' | tr -cd '[:alnum:]_.-')"
LAB_DIR="${BASE_DIR}/${SAFE_NAME}"

mkdir -p "${LAB_DIR}"

copy_template() {
  local src="$1"
  local dst="$2"
  if [[ -e "${dst}" ]]; then
    echo "[SKIP] Existe: ${dst}"
    return 0
  fi
  sed "s/{{NOMBRE}}/${SAFE_NAME}/g" "${src}" > "${dst}"
  echo "[OK] Creado: ${dst}"
}

copy_template "${TEMPLATE_DIR}/lab_README.md" "${LAB_DIR}/README.md"
copy_template "${TEMPLATE_DIR}/notas.md" "${LAB_DIR}/notas.md"
copy_template "${TEMPLATE_DIR}/evidencias.md" "${LAB_DIR}/evidencias.md"
copy_template "${TEMPLATE_DIR}/hallazgos.md" "${LAB_DIR}/hallazgos.md"
copy_template "${TEMPLATE_DIR}/relevo.md" "${LAB_DIR}/relevo.md"

echo "[OK] Expediente listo: ${LAB_DIR}"
echo "[INFO] No se ejecutaron escaneos ni comandos ofensivos."
