# Arquitectura visual del flujo de trabajo

```mermaid
flowchart LR
  U[Usuario / Operador] --> R[Repo hacking]
  R --> D[docs]
  R --> T[templates]
  R --> S[scripts seguros]
  R --> E[examples]
  S --> K[kali-lab VirtualBox]
  K --> L[Laboratorio autorizado]
  D --> I[Informe / Relevo]
  T --> I
```

## Capas

- **Repo:** metodología, plantillas y scripts auxiliares.
- **Kali Lab:** entorno técnico controlado.
- **Laboratorio/cliente:** solo objetivos autorizados.
- **Informe/relevo:** trazabilidad y continuidad.
