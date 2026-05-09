# Hacking Ético & Pentesting Autorizado

Repositorio personal para organizar metodología, scripts auxiliares seguros y documentación de laboratorios de **Red Team ético**, **HTB/THM/CTF**, pruebas de concepto controladas y proyectos de pentesting **siempre autorizados**.

> Este repositorio no es para atacar terceros. Todo uso debe estar limitado a laboratorios, entornos propios o clientes con autorización explícita y alcance definido.

## Objetivos

- Mantener una metodología clara para laboratorios y trabajos autorizados.
- Reutilizar plantillas profesionales para notas, evidencias, hallazgos, informes y relevos.
- Centralizar scripts seguros de apoyo operativo: estado de Kali, arranque de VM, comprobación SSH, creación de expedientes y logging de comandos.
- Facilitar documentación visual con Mermaid y diagramas en Markdown.
- Separar aprendizaje, laboratorios y documentación de cliente de cualquier secreto o evidencia privada.

## Estructura

```text
.
├── docs/                         # Metodología y documentación visual
│   ├── metodologia.md
│   ├── flujo_laboratorio.md
│   ├── flujo_cliente_autorizado.md
│   ├── kali_lab.md
│   ├── evidencias.md
│   └── visual/arquitectura.md
├── templates/                    # Plantillas reutilizables
│   ├── lab_README.md
│   ├── notas.md
│   ├── evidencias.md
│   ├── hallazgos.md
│   ├── relevo.md
│   └── informe.md
├── scripts/                      # Scripts auxiliares seguros
│   ├── kali_status.sh
│   ├── kali_start.sh
│   ├── kali_ssh_check.sh
│   ├── lab_init.sh
│   └── safe_command_log.sh
├── examples/
│   └── demo-lab-sin-datos-reales/
└── README.md
```

## Uso rápido

### Crear expediente local de laboratorio

```bash
./scripts/lab_init.sh demo-lab
```

Crea una carpeta local con plantillas base, sin ejecutar escaneos ni herramientas ofensivas.

### Comprobar VM Kali de laboratorio

```bash
./scripts/kali_status.sh
./scripts/kali_start.sh
./scripts/kali_ssh_check.sh
```

Los scripts solo comprueban estado de VirtualBox/SSH local. No hacen reconocimiento ni pentesting.

### Registrar comandos de forma segura

```bash
./scripts/safe_command_log.sh ./labs/demo-lab/notas.md "whoami" "Comprobación de usuario en entorno local"
```

Este script ejecuta un comando local y guarda comando, fecha, descripción, código de salida y salida en Markdown.

## Reglas de seguridad

1. Trabajar solo en entornos propios, HTB/THM/CTF o clientes con autorización explícita.
2. No incluir secretos reales, tokens, claves privadas, `.env`, dumps, PCAPs privados o datos de clientes.
3. No subir evidencias privadas al repositorio.
4. Documentar alcance antes de ejecutar cualquier técnica activa.
5. Separar hechos, hipótesis y resultados reproducibles.
6. Mantener scripts auxiliares simples, auditables y no ofensivos.

## Carpetas históricas existentes

Este repo ya contenía carpetas y scripts de aprendizaje como `Host/`, `Tor/`, `Web/`, `XML-RPC/`, `dns/`, `doxeo/`, `estudio/`, `github/` y `music/`. No se han borrado. La nueva estructura añade una capa ordenada para laboratorios y documentación profesional.

## Disclaimer

Contenido con fines educativos y de seguridad defensiva/ofensiva autorizada. No uses este material contra sistemas sin permiso explícito.
