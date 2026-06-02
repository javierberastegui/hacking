# Checklist defensiva para revisar tu router WiFi

Recurso local y defensivo para acompañar un artículo sobre qué revisar en el router de casa después de una alerta o sospecha.

Está pensado para usuarios que quieren ordenar una revisión básica de su propio router, documentar cambios y saber cuándo contactar con su operador. No realiza escaneos, no analiza tráfico, no prueba credenciales, no abre paneles, no llama a servicios externos y no recoge datos sensibles.

## Contenido

- `checklist_revision_router_wifi.md`: checklist práctica para revisar el router propio desde canales oficiales.
- `plantilla_registro_revision_router.md`: plantilla manual para anotar cambios sin escribir contraseñas completas ni datos sensibles.
- `generar_checklist_router.py`: helper local que genera una checklist Markdown imprimible con recordatorios defensivos.

## Uso rápido

Ver ayuda del helper:

```bash
python3 recursos/checklist-router-wifi/generar_checklist_router.py --help
```

Generar una checklist básica:

```bash
python3 recursos/checklist-router-wifi/generar_checklist_router.py --salida /tmp/checklist_router_wifi.md
```

Generar una checklist con recordatorios opcionales:

```bash
python3 recursos/checklist-router-wifi/generar_checklist_router.py   --etiqueta "router de casa"   --alerta "aviso del operador"   --red-invitados   --revisar-cuentas   --salida /tmp/checklist_router_wifi.md
```

## Seguridad y alcance

Este recurso es local-only:

- No hace llamadas de red.
- No escanea WiFi, puertos, Bluetooth, dispositivos ni redes cercanas.
- No captura tráfico ni analiza paquetes.
- No automatiza acceso al panel del router.
- No pide contraseñas, tokens, cookies, IPs públicas, MAC reales ni datos personales.
- No sustituye al soporte del ISP, al fabricante del router ni a un profesional de seguridad.

El objetivo es revisar con calma el router propio desde canales oficiales: contraseña de administración, clave WiFi, WPA2/WPA3, WPS, administración remota, firmware, red de invitados, dispositivos reconocidos, DNS y registro de cambios.

## Encaje editorial

Puede acompañar un artículo sobre `router wifi` como recurso práctico para:

- Responder a una alerta sin tocar redes ajenas.
- Evitar compras o herramientas innecesarias.
- Documentar qué se ha revisado y qué queda pendiente.
- Reforzar cuentas críticas relacionadas, como correo, nube, panel del operador o gestor de contraseñas.
- Decidir cuándo contactar con el operador por canales oficiales.

## URL pública esperada

Tras commit y push a `main`, el recurso debería quedar disponible en:

https://github.com/javierberastegui/hacking/tree/main/recursos/checklist-router-wifi

## Validación local recomendada

Desde la raíz del repo:

```bash
cd /home/lokky/hacking
python3 recursos/checklist-router-wifi/generar_checklist_router.py --help
python3 -m py_compile recursos/checklist-router-wifi/generar_checklist_router.py
python3 recursos/checklist-router-wifi/generar_checklist_router.py --etiqueta "router de casa" --alerta "aviso del operador" --red-invitados --revisar-cuentas --salida /tmp/checklist_router_wifi.md
test -s /tmp/checklist_router_wifi.md
git diff --check
git status --short
```

## CTA sugerida para el artículo

También he dejado un recurso práctico en el repo de hacking: una checklist, una plantilla y un helper local para revisar tu propio router WiFi después de una alerta sin hacer llamadas externas, escanear redes ni guardar secretos.

Recurso en GitHub: https://github.com/javierberastegui/hacking/tree/main/recursos/checklist-router-wifi
