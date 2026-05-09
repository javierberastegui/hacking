# Flujo para cliente autorizado

## Precondiciones

- Contrato o permiso escrito.
- Alcance firmado.
- Contacto de emergencia.
- Ventana de pruebas.
- Reglas de engagement.

## Flujo operativo

```mermaid
flowchart TD
  A[Kickoff] --> B[Alcance y ROE]
  B --> C[Preparación de entorno]
  C --> D[Reconocimiento permitido]
  D --> E[Pruebas técnicas]
  E --> F{Hallazgo validado?}
  F -- Sí --> G[Evidencia y severidad]
  F -- No --> H[Descartar o documentar hipótesis]
  G --> I[Informe]
  H --> I
  I --> J[Entrega y cierre]
```

## Datos que nunca deben subirse al repo

- Credenciales reales.
- Datos personales.
- Dumps de bases de datos.
- PCAPs de cliente.
- Capturas con información sensible.
- Informes privados finales.

Usar un repositorio/almacenamiento privado del cliente o gestor documental autorizado.
