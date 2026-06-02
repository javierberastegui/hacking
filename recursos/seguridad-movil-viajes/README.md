# Seguridad del móvil en viajes

Recurso defensivo y local para preparar un viaje con el móvil sin caer en mitos sobre WiFi público, Bluetooth, VPN o copias de seguridad.

Está pensado para lectores que quieren revisar hábitos básicos antes de salir, durante el viaje y si el móvil se pierde o muestra actividad sospechosa. No realiza escaneos, no analiza redes, no llama a servicios externos y no recoge datos personales.

## Contenido

- `checklist_seguridad_movil_viajes.md`: lista práctica para revisar antes, durante y después del viaje.
- `plantilla_plan_viaje_seguro.md`: plantilla Markdown para preparar un plan propio sin escribir secretos.
- `generar_checklist_viaje.py`: helper local que genera una checklist imprimible desde opciones no sensibles.

## Uso rápido

Ver ayuda del helper:

```bash
python3 generar_checklist_viaje.py --help
```

Generar una checklist básica:

```bash
python3 generar_checklist_viaje.py --destino "viaje" --dias 7 --salida checklist_viaje.md
```

Generar una checklist con recordatorios opcionales:

```bash
python3 generar_checklist_viaje.py --destino "viaje" --dias 10 --usa-passkeys --lleva-powerbank --lleva-portatil --salida checklist_viaje.md
```

## Seguridad y alcance

Este recurso es local-only:

- No hace llamadas de red.
- No escanea WiFi, Bluetooth, NFC, USB ni dispositivos.
- No pide credenciales, tokens, números de teléfono, correos reales ni datos bancarios.
- No sustituye soporte de tu banco, operador, proveedor cloud o administrador de sistemas.
- No promete protección total: ayuda a ordenar hábitos defensivos.

## Encaje editorial

Puede acompañar un artículo sobre seguridad móvil en viajes como recurso práctico para:

- Preparar cuentas críticas antes de salir.
- Reducir exposición al cargar el móvil o usar redes públicas.
- Usar VPN con expectativas realistas.
- Mantener copias y recuperación sin guardar secretos en la plantilla.
- Responder con calma ante pérdida o robo del dispositivo.

## URL pública esperada

Tras commit y push a `main`, el recurso debería quedar disponible en:

https://github.com/javierberastegui/hacking/tree/main/recursos/seguridad-movil-viajes

## Validación local recomendada

Desde la raíz del repo:

```bash
cd /home/lokky/hacking
python3 recursos/seguridad-movil-viajes/generar_checklist_viaje.py --help
python3 -m py_compile recursos/seguridad-movil-viajes/generar_checklist_viaje.py
python3 recursos/seguridad-movil-viajes/generar_checklist_viaje.py --destino "viaje" --dias 10 --usa-passkeys --lleva-powerbank --lleva-portatil --salida /tmp/checklist_viaje_seguro.md
test -s /tmp/checklist_viaje_seguro.md
git diff --check
git status --short
```

## CTA sugerida para el artículo

También he dejado un recurso práctico en el repo de hacking: una checklist, una plantilla y un helper local para preparar la seguridad del móvil antes de viajar sin hacer llamadas externas ni probar redes de terceros.

Recurso en GitHub: https://github.com/javierberastegui/hacking/tree/main/recursos/seguridad-movil-viajes
