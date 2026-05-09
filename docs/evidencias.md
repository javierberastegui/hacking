# Gestión de evidencias

## Objetivo

Mantener evidencias útiles, reproducibles y seguras sin exponer datos reales o sensibles.

## Tipos de evidencia

- Salida de comandos filtrada.
- Capturas de pantalla sin datos sensibles.
- Extractos de logs autorizados.
- Hashes de archivos de laboratorio.
- Pasos de reproducción.

## Convención de nombres

```text
YYYYMMDD_HHMM_tipo_descripcion.ext
```

Ejemplos:

- `20260509_1200_nmap_tcp_top100.txt`
- `20260509_1215_http_login_screenshot.png`

## Reglas

- No subir PCAPs privados.
- No subir dumps reales.
- No subir credenciales reales.
- Redactar tokens, emails, IPs de cliente si no son necesarias.
- Asociar cada evidencia a un hallazgo o nota.
