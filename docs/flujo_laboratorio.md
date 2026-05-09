# Flujo de laboratorio HTB/THM/CTF

## Objetivo

Estandarizar el trabajo en laboratorios autorizados sin mezclar datos reales.

## Flujo

```mermaid
sequenceDiagram
  participant U as Usuario
  participant H as Hermes/Repo
  participant K as Kali Lab
  participant T as Target HTB/THM/CTF
  U->>H: Indica nombre del lab e IP objetivo
  H->>H: Crea expediente y plantillas
  H->>K: Comprueba SSH/entorno
  H->>H: Prepara plan de enumeración
  U->>H: Autoriza ejecución
  H->>T: Ejecuta comandos dentro del alcance
  H->>H: Documenta resultados/evidencias
```

## Estados

- `preparacion`: expediente creado, sin escaneos.
- `enumeracion`: reconocimiento autorizado en curso.
- `validacion`: hipótesis contrastadas.
- `explotacion_controlada`: solo si el laboratorio lo permite.
- `cierre`: informe, relevo y lecciones aprendidas.

## Normas

- No ejecutar escaneos hasta tener IP objetivo.
- No atacar fuera del entorno del laboratorio.
- Registrar todos los comandos relevantes.
- Guardar credenciales solo si son del laboratorio.
