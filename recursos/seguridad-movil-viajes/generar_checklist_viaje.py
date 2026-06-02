#!/usr/bin/env python3
"""Genera una checklist local de seguridad móvil para viajes.

El script no hace llamadas de red, no pide secretos y solo escribe un archivo
Markdown local con recomendaciones defensivas generales.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera una checklist Markdown local para preparar el móvil antes de viajar."
    )
    parser.add_argument(
        "--destino",
        default="viaje",
        help="Etiqueta genérica del viaje. Evita escribir datos personales o direcciones exactas.",
    )
    parser.add_argument(
        "--dias",
        type=int,
        default=7,
        help="Duración aproximada del viaje en días. Se usa solo para priorizar recordatorios.",
    )
    parser.add_argument(
        "--salida",
        default="checklist_viaje_seguro.md",
        help="Ruta del archivo Markdown local que se generará.",
    )
    parser.add_argument(
        "--usa-passkeys",
        action="store_true",
        help="Añade recordatorio de llave/passkey para cuentas críticas.",
    )
    parser.add_argument(
        "--lleva-powerbank",
        action="store_true",
        help="Añade recordatorio para cargar con power bank o enchufe propio.",
    )
    parser.add_argument(
        "--lleva-portatil",
        action="store_true",
        help="Añade recordatorios básicos si también llevas portátil o tablet.",
    )
    return parser.parse_args()


def build_checklist(args: argparse.Namespace) -> str:
    destino = args.destino.strip() or "viaje"
    dias = max(args.dias, 1)

    optional_items: list[str] = []
    if args.usa_passkeys:
        optional_items.append(
            "- [ ] Probar antes de salir que la llave FIDO2/passkey funciona en correo, nube o gestor de contraseñas."
        )
    if args.lleva_powerbank:
        optional_items.append(
            "- [ ] Cargar la power bank y llevar cable propio para evitar depender de puertos USB públicos."
        )
    if args.lleva_portatil:
        optional_items.extend(
            [
                "- [ ] Actualizar portátil/tablet y activar bloqueo automático.",
                "- [ ] Revisar cifrado de disco y copia de seguridad de documentos necesarios.",
            ]
        )
    if dias >= 14:
        optional_items.append(
            "- [ ] Planificar una revisión intermedia de copias, sesiones y alertas si el viaje dura varias semanas."
        )

    optional_block = "\n".join(optional_items) if optional_items else "- [ ] Sin extras seleccionados."

    return dedent(
        f"""
        # Checklist de seguridad móvil para {destino}

        Duración aproximada: {dias} día(s)

        Aviso: este archivo no debe contener contraseñas, códigos 2FA, números de tarjeta,
        documentos personales ni datos de terceros.

        ## Antes de salir

        - [ ] Actualizar sistema operativo y aplicaciones principales.
        - [ ] Activar bloqueo de pantalla fuerte y borrado/bloqueo remoto.
        - [ ] Hacer copia de seguridad reciente y comprobar recuperación.
        - [ ] Revisar 2FA/passkeys en correo, banca, nube y gestor de contraseñas.
        - [ ] Cerrar sesiones antiguas o desconocidas.
        - [ ] Preparar contactos de soporte de operador, banco y cuentas críticas.
        {optional_block}

        ## Durante el viaje

        - [ ] Priorizar datos móviles o redes conocidas para operaciones sensibles.
        - [ ] Tratar el WiFi público como red no confiable.
        - [ ] Usar VPN con expectativas realistas: ayuda con redes no confiables, pero no evita phishing, malware, robo físico ni claves débiles.
        - [ ] Evitar instalar apps desde enlaces inesperados, SMS o QR no verificados.
        - [ ] Evitar cargar en puertos USB desconocidos si puedes usar enchufe de pared o batería externa.
        - [ ] Desactivar conexiones que no uses si prefieres reducir exposición.

        ## Si pierdes el móvil o detectas actividad sospechosa

        - [ ] Bloquear el dispositivo con la herramienta oficial del fabricante o cuenta asociada.
        - [ ] Contactar con el operador para proteger SIM/eSIM.
        - [ ] Cambiar contraseñas críticas desde un dispositivo confiable.
        - [ ] Revocar sesiones abiertas en correo, nube, banca, redes sociales y mensajería.
        - [ ] Avisar al banco si había tarjetas o wallet configuradas.
        - [ ] Documentar acciones realizadas sin incluir secretos.

        ## Límites seguros

        Esta checklist no incluye pruebas contra redes, Bluetooth, USB, NFC ni dispositivos de terceros.
        Es una guía defensiva de preparación y respuesta.
        """
    ).strip() + "\n"


def main() -> None:
    args = parse_args()
    output_path = Path(args.salida).expanduser()
    output_path.write_text(build_checklist(args), encoding="utf-8")
    print(f"Checklist creada en: {output_path}")


if __name__ == "__main__":
    main()
