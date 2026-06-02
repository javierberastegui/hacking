#!/usr/bin/env python3
"""Genera una checklist local para revisar un router WiFi propio.

El script no hace llamadas de red, no escanea dispositivos, no pide secretos y
solo escribe un archivo Markdown local con recomendaciones defensivas generales.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera una checklist Markdown local para revisar tu propio router WiFi."
    )
    parser.add_argument(
        "--etiqueta",
        default="router de casa",
        help="Etiqueta genérica del router. Evita datos personales, direcciones, IPs o identificadores reales.",
    )
    parser.add_argument(
        "--alerta",
        default="revisión preventiva",
        help="Motivo genérico de la revisión, sin pegar mensajes completos ni datos sensibles.",
    )
    parser.add_argument(
        "--salida",
        default="checklist_router_wifi.md",
        help="Ruta del archivo Markdown local que se generará.",
    )
    parser.add_argument(
        "--red-invitados",
        action="store_true",
        help="Añade recordatorio específico para revisar o crear red de invitados.",
    )
    parser.add_argument(
        "--revisar-cuentas",
        action="store_true",
        help="Añade recordatorios para cuentas críticas relacionadas con el router y la red doméstica.",
    )
    parser.add_argument(
        "--contactar-isp",
        action="store_true",
        help="Añade bloque de preparación para contactar con el operador por canales oficiales.",
    )
    return parser.parse_args()


def safe_line(value: str, fallback: str) -> str:
    cleaned = " ".join(value.strip().split())
    return cleaned or fallback


def build_checklist(args: argparse.Namespace) -> str:
    etiqueta = safe_line(args.etiqueta, "router de casa")
    alerta = safe_line(args.alerta, "revisión preventiva")

    optional_items: list[str] = []
    if args.red_invitados:
        optional_items.extend(
            [
                "- [ ] Revisar si conviene una red de invitados para visitas o dispositivos menos confiables.",
                "- [ ] Comprobar que la red de invitados no da acceso innecesario a equipos personales.",
            ]
        )
    if args.revisar_cuentas:
        optional_items.extend(
            [
                "- [ ] Revisar correo principal, cuenta del operador, nube y gestor de contraseñas.",
                "- [ ] Activar 2FA/passkeys en cuentas críticas cuando esté disponible.",
                "- [ ] Cerrar sesiones desconocidas desde paneles oficiales.",
            ]
        )
    if args.contactar_isp:
        optional_items.extend(
            [
                "- [ ] Preparar contrato, app oficial o número de soporte del ISP antes de llamar.",
                "- [ ] Explicar el síntoma sin compartir contraseñas completas ni códigos de verificación.",
            ]
        )
    if not optional_items:
        optional_items.append("- [ ] Sin extras seleccionados: completa primero la revisión básica.")

    optional_block = "\n".join(optional_items)

    return dedent(
        f"""
        # Checklist defensiva para {etiqueta}

        Motivo declarado: {alerta}

        Aviso: este archivo no debe contener contraseñas, códigos 2FA, tokens,
        IPs públicas sensibles, direcciones físicas ni datos personales de terceros.
        Úsalo solo para tu propio router o equipos sobre los que tengas autorización.

        ## Acceso seguro

        - [ ] Entrar solo desde la app oficial, panel indicado por el fabricante/ISP o documentación propia.
        - [ ] No usar enlaces recibidos por SMS, email o llamadas inesperadas para acceder al panel.
        - [ ] Hacer la revisión desde un dispositivo propio y actualizado.

        ## Configuración del router

        - [ ] Revisar/cambiar contraseña de administración si es débil, antigua o compartida.
        - [ ] Revisar/cambiar clave WiFi si está reutilizada, expuesta o es demasiado corta.
        - [ ] Confirmar WPA2/WPA3 cuando el router lo permita.
        - [ ] Desactivar WPS si no se usa.
        - [ ] Desactivar administración remota si no es necesaria.
        - [ ] Revisar firmware desde canal oficial.
        - [ ] Revisar DNS y anotar si coincide con una elección consciente.

        ## Dispositivos y cambios

        - [ ] Revisar dispositivos conectados desde el panel oficial, sin escanear redes.
        - [ ] Identificar equipos propios por nombre reconocible cuando sea posible.
        - [ ] Si hay equipos desconocidos, cambiar clave WiFi y reconectar equipos propios con calma.
        - [ ] Anotar fecha, motivo y cambios sin escribir secretos completos.

        ## Recordatorios opcionales

        {optional_block}

        ## Cuándo parar y pedir ayuda

        - [ ] Contactar con el operador si hay cambios no reconocidos en firmware, DNS o administración remota.
        - [ ] Contactar con servicios afectados si la alerta vino de phishing y se introdujeron datos.
        - [ ] Pedir ayuda profesional si hay señales repetidas o cuentas críticas comprometidas.

        ## Límites seguros

        Esta checklist no hace pruebas contra redes o dispositivos. No incluye escaneo,
        captura de tráfico, cracking WiFi, explotación, bypass ni automatización de acceso.
        """
    ).strip() + "\n"


def main() -> None:
    args = parse_args()
    output_path = Path(args.salida).expanduser()
    output_path.write_text(build_checklist(args), encoding="utf-8")
    print(f"Checklist creada en: {output_path}")


if __name__ == "__main__":
    main()
