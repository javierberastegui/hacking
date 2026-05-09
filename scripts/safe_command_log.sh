#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="${1:-}"
COMMAND_TO_RUN="${2:-}"
DESCRIPTION="${3:-Sin descripción}"

if [[ -z "${LOG_FILE}" || -z "${COMMAND_TO_RUN}" ]]; then
  echo "Uso: $0 <archivo_markdown> <comando> [descripcion]"
  exit 1
fi

mkdir -p "$(dirname "${LOG_FILE}")"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
TMP_OUTPUT="$(mktemp)"
set +e
bash -lc "${COMMAND_TO_RUN}" >"${TMP_OUTPUT}" 2>&1
EXIT_CODE=$?
set -e

{
  echo
  echo "## Comando registrado - ${TIMESTAMP}"
  echo
  echo "- Descripción: ${DESCRIPTION}"
  echo "- Código de salida: ${EXIT_CODE}"
  echo
  echo '```bash'
  echo "${COMMAND_TO_RUN}"
  echo '```'
  echo
  echo '```text'
  cat "${TMP_OUTPUT}"
  echo '```'
} >> "${LOG_FILE}"

rm -f "${TMP_OUTPUT}"
echo "[OK] Registro añadido a ${LOG_FILE}"
exit "${EXIT_CODE}"
