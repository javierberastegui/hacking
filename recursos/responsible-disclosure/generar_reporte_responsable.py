#!/usr/bin/env python3
"""Genera una plantilla local de reporte para divulgación responsable.

Este helper es deliberadamente defensivo y local:
- no realiza llamadas de red;
- no escanea, rastrea ni prueba sistemas;
- no genera payloads ni PoC ejecutables;
- no recopila datos de acceso, material de sesión ni datos personales reales;
- solo ayuda a ordenar un reporte Markdown con campos seguros.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

PLACEHOLDER = "Completar sin incluir datos sensibles, datos de acceso ni datos personales reales."


def safe(value: str | None) -> str:
    return value.strip() if value and value.strip() else PLACEHOLDER


def build_markdown(args: argparse.Namespace) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""# Borrador local de reporte de divulgación responsable

Generado: {generated_at}

> Uso defensivo: completa este documento de forma local. No incluyas datos de acceso, material de sesión, datos personales reales, información de terceros ni pasos que permitan explotar el problema fuera de un entorno autorizado.

## 1. Resumen

- Título breve: {safe(args.titulo)}
- Servicio, producto o activo afectado dentro del alcance autorizado: {safe(args.activo)}
- Tipo de problema observado, descrito de forma general: {safe(args.tipo)}
- Fecha aproximada de observación: {safe(args.fecha)}

## 2. Confirmación de alcance y límites

- [ ] He revisado el canal oficial, security.txt, programa de disclosure o política aplicable.
- [ ] El activo indicado parece estar dentro del alcance autorizado.
- [ ] Me he detenido al confirmar la señal mínima necesaria.
- [ ] No he accedido a datos de terceros ni he intentado ampliar impacto.
- [ ] No he realizado escaneo masivo, explotación adicional, persistencia ni evasión.
- [ ] No publicaré detalles técnicos hasta que exista coordinación razonable.

Notas de alcance:

{safe(args.alcance)}

## 3. Impacto explicado sin exagerar

Describe el riesgo en lenguaje claro, sin alarmismo y sin promesas absolutas.

{safe(args.impacto)}

## 4. Evidencia mínima y redactada

Incluye solo evidencia necesaria para que el equipo reproduzca o entienda el problema sin exponer datos sensibles.

- Capturas redactadas: Sí / No / Pendiente
- Datos sensibles ocultados: Sí / No / No aplica
- Identificadores de terceros eliminados: Sí / No / No aplica
- Material de sesión o datos sensibles incluidos: No

Descripción de evidencia:

{safe(args.evidencia)}

## 5. Pasos generales no explotables

Redacta pasos de alto nivel, suficientes para orientar al equipo responsable, pero evita payloads, cadenas exactas peligrosas, automatización o instrucciones para atacar sistemas ajenos.

1. {safe(args.paso_uno)}
2. {safe(args.paso_dos)}
3. {safe(args.paso_tres)}

## 6. Mitigación sugerida, si procede

{safe(args.mitigacion)}

## 7. Contacto y seguimiento

- Canal oficial utilizado: {safe(args.canal)}
- Fecha de envío prevista o realizada: {safe(args.fecha_envio)}
- Referencia interna o ticket, si existe: {safe(args.referencia)}
- Próximo seguimiento razonable: esperar respuesta antes de publicar o ampliar detalles.

## 8. Lista de no hacer

- [ ] No incluir datos de acceso, material de sesión, llaves de servicio ni cabeceras de autorización.
- [ ] No incluir datos personales reales de terceros.
- [ ] No adjuntar bases de datos, volcados, logs completos ni capturas sin redactar.
- [ ] No probar otros activos fuera del alcance.
- [ ] No ejecutar escaneos, fuzzing o automatización contra terceros.
- [ ] No usar tono amenazante, presión pública ni exigencias económicas fuera de un programa formal.

## Aviso

Esta plantilla no es asesoramiento legal ni sustituye a la política oficial del servicio afectado. Si hay duda sobre autorización, datos sensibles, impacto legal o riesgo para terceros, detente y busca orientación profesional antes de continuar.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Genera un borrador Markdown local para reportar una vulnerabilidad "
            "de forma responsable, sin llamadas externas ni pruebas técnicas."
        )
    )
    parser.add_argument("--titulo", help="Título breve del hallazgo, sin datos sensibles.")
    parser.add_argument("--activo", help="Servicio, producto o activo dentro del alcance autorizado.")
    parser.add_argument("--tipo", help="Descripción general del tipo de problema observado.")
    parser.add_argument("--fecha", help="Fecha aproximada de observación.")
    parser.add_argument("--alcance", help="Notas sobre canal oficial, política o alcance autorizado.")
    parser.add_argument("--impacto", help="Impacto descrito de forma clara y no alarmista.")
    parser.add_argument("--evidencia", help="Resumen de evidencia mínima redactada.")
    parser.add_argument("--paso-uno", help="Primer paso general no explotable.")
    parser.add_argument("--paso-dos", help="Segundo paso general no explotable.")
    parser.add_argument("--paso-tres", help="Tercer paso general no explotable.")
    parser.add_argument("--mitigacion", help="Mitigación sugerida, si procede.")
    parser.add_argument("--canal", help="Canal oficial usado para enviar el reporte.")
    parser.add_argument("--fecha-envio", help="Fecha de envío prevista o realizada.")
    parser.add_argument("--referencia", help="Referencia o ticket, si existe.")
    parser.add_argument("--output", "-o", help="Ruta del archivo Markdown a crear. Si se omite, imprime por pantalla.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    markdown = build_markdown(args)
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Borrador creado localmente: {output_path}")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
