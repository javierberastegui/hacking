#!/usr/bin/env python3
"""Genera una plantilla local en Markdown para documentar un SMS sospechoso.

Este helper es deliberadamente defensivo y local:
- no abre enlaces;
- no valida dominios;
- no realiza peticiones de red;
- no analiza infraestructura de terceros;
- no envía datos a ningún servicio.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def build_markdown(args: argparse.Namespace) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""# Registro local de SMS sospechoso

Generado: {generated_at}

> Uso defensivo: completa este documento de forma local. No abras enlaces del SMS, no llames a números incluidos en el mensaje y no introduzcas datos para comprobar si la página es real.

## Datos básicos

- Fecha y hora de recepción: {args.fecha or ""}
- Remitente visible: {args.remitente or ""}
- Entidad que aparenta ser: {args.entidad or ""}
- Resumen del mensaje: {args.resumen or ""}
- Dominio/enlace visible como texto, sin abrirlo: {args.enlace_visible or ""}
- Acción que pedía el SMS: {args.accion_solicitada or ""}

## Exposición

- ¿He hecho clic?: {args.click or "Sí / No"}
- ¿He introducido datos?: {args.datos or "Sí / No"}
- Qué datos he introducido, si aplica:
  - Usuario/correo:
  - Contraseña:
  - DNI/NIE u otro identificador:
  - Teléfono:
  - Dirección:
  - Datos de tarjeta/cuenta:
  - Código SMS/OTP/clave de firma:
  - Otros:
- ¿He descargado o instalado algo?: Sí / No
- ¿He realizado o autorizado algún pago?: Sí / No
- Importe, fecha y método de pago, si aplica:

## Acciones recomendadas por canales oficiales

Marca lo que ya hayas hecho. Usa siempre canales independientes del SMS: app oficial instalada previamente, web escrita manualmente, teléfono de la tarjeta/factura/contrato o soporte verificado.

- [ ] Cortar la interacción con el SMS: no responder, no abrir enlaces y no instalar apps.
- [ ] Hacer capturas si se puede sin volver a abrir enlaces ni mostrar datos sensibles innecesarios.
- [ ] Verificar la incidencia desde la app, web o teléfono oficial de la entidad.
- [ ] Cambiar contraseña desde sitio/app oficial si se introdujeron credenciales.
- [ ] Revisar 2FA, passkeys, sesiones activas y métodos de recuperación si aplica.
- [ ] Contactar con el banco por canal oficial si se introdujeron datos bancarios, códigos OTP o se autorizó un pago.
- [ ] Revisar movimientos y pedir referencia de reclamación si hubo cargos.
- [ ] Valorar denuncia o reporte si hubo pérdida económica, suplantación o uso indebido de datos.

## Evidencias conservadas

- Capturas de pantalla:
- Número/remitente visible:
- Fecha y hora:
- Comunicaciones con banco/operador/entidad:
- Número de referencia de reclamación o denuncia, si existe:

## Notas adicionales


## Límites de seguridad

Este registro no detecta fraudes automáticamente y no sustituye a tu banco, operador, entidad afectada, policía ni asesoramiento jurídico/técnico especializado. Su objetivo es ayudarte a ordenar información y reducir el riesgo de actuar desde el propio SMS.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera una plantilla Markdown local para registrar un SMS sospechoso sin realizar llamadas externas."
    )
    parser.add_argument("--fecha", help="Fecha y hora de recepción del SMS, si se conoce.")
    parser.add_argument("--remitente", help="Número, alias o nombre visible del remitente.")
    parser.add_argument("--entidad", help="Entidad que el SMS aparenta representar.")
    parser.add_argument("--resumen", help="Resumen breve del contenido del SMS.")
    parser.add_argument("--enlace-visible", help="Dominio o enlace visible, copiado como texto y sin abrirlo.")
    parser.add_argument("--accion-solicitada", help="Qué pedía hacer el SMS: pagar, iniciar sesión, actualizar datos, llamar, etc.")
    parser.add_argument("--click", choices=["Sí", "No", "No lo sé"], help="Indica si se hizo clic.")
    parser.add_argument("--datos", choices=["Sí", "No", "No lo sé"], help="Indica si se introdujeron datos.")
    parser.add_argument("--output", "-o", help="Ruta del archivo Markdown a crear. Si se omite, imprime por pantalla.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    markdown = build_markdown(args)
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Plantilla creada localmente: {output_path}")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
