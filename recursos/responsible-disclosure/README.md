# Recurso defensivo: responsible disclosure

Recurso público y local para acompañar el artículo:

- Tema: cómo reportar una vulnerabilidad de forma responsable sin meterte en problemas.
- Enfoque: límites, autorización, evidencia mínima, canal oficial y comunicación clara.

## Propósito

Esta carpeta reúne una checklist, una plantilla manual y un pequeño helper local para ayudar a preparar un reporte de divulgación responsable sin cruzar límites técnicos, legales o éticos.

El objetivo no es encontrar vulnerabilidades, explotarlas ni automatizar pruebas. El valor del recurso está en ordenar lo que ya se observó de forma autorizada, reducir exposición de datos sensibles y comunicarlo por el canal correcto.

## Contenido

- `generar_reporte_responsable.py`: script local que genera un borrador Markdown de reporte a partir de campos manuales opcionales.
- `checklist_divulgacion_responsable.md`: checklist defensiva para revisar límites antes de enviar un reporte.
- `plantilla_reporte_responsable.md`: plantilla manual para copiar, imprimir o completar en una nota local.
- `guia_redaccion_evidencias.md`: guía breve para redactar evidencias sin exponer datos sensibles ni datos personales.

## Límites de seguridad

Este recurso es exclusivamente defensivo, educativo y local.

No hace ni debe hacer lo siguiente:

- escanear, rastrear, fuzzear o probar sistemas;
- abrir URLs, consultar endpoints o hacer llamadas de red;
- generar payloads, PoC ejecutables o pasos de explotación;
- recopilar datos de acceso, material de sesión, cabeceras de autorización o llaves de servicio;
- almacenar datos personales reales de terceros;
- automatizar contacto, presión pública o publicación;
- sustituir asesoramiento legal, soporte oficial o coordinación con el equipo responsable.

## Uso rápido

Mostrar ayuda:

```bash
python3 recursos/responsible-disclosure/generar_reporte_responsable.py --help
```

Imprimir una plantilla vacía por pantalla:

```bash
python3 recursos/responsible-disclosure/generar_reporte_responsable.py
```

Crear un borrador local con datos de ejemplo seguros:

```bash
python3 recursos/responsible-disclosure/generar_reporte_responsable.py \
  --titulo "Posible error de control de acceso en entorno propio" \
  --activo "Panel de ejemplo dentro del alcance autorizado" \
  --tipo "Comportamiento inesperado al consultar una sección propia" \
  --fecha "2026-05-31" \
  --alcance "Revisada la política de seguridad; no se probaron activos fuera de alcance" \
  --impacto "Podría permitir ver información que no corresponde al usuario autenticado" \
  --evidencia "Captura redactada con identificadores ficticios y sin datos de terceros" \
  --paso-uno "Iniciar sesión en una cuenta propia de prueba" \
  --paso-dos "Abrir la sección afectada dentro del entorno autorizado" \
  --paso-tres "Observar el resultado anómalo sin acceder a datos ajenos" \
  --canal "security@example.invalid" \
  --output /tmp/reporte_responsable_demo.md
```

Nota: `example.invalid` es un dominio reservado para documentación. No se abre ni se consulta.

## Flujo recomendado

1. Revisa si existe política oficial, `security.txt`, programa de disclosure o canal de seguridad.
2. Confirma que lo observado está dentro del alcance autorizado.
3. Detente al obtener la evidencia mínima necesaria; no amplíes impacto.
4. Redacta capturas, IDs, correos, material de sesión y cualquier dato sensible.
5. Explica impacto y pasos de forma general, sin payloads ni instrucciones de abuso.
6. Envía el reporte por el canal oficial con tono claro y colaborativo.
7. Espera coordinación antes de publicar detalles técnicos.

## CTA para el artículo

También he dejado un recurso práctico en el repo de hacking: una checklist, una plantilla y un helper local para preparar un reporte de responsible disclosure sin exponer datos sensibles ni hacer llamadas externas.

Recurso en GitHub: https://github.com/javierberastegui/hacking/tree/main/recursos/responsible-disclosure

## URL pública esperada

Cuando esta carpeta se sincronice con `origin/main`, el recurso debería estar disponible en:

https://github.com/javierberastegui/hacking/tree/main/recursos/responsible-disclosure

## Aviso

Este recurso no convierte una prueba no autorizada en autorizada. Si no tienes claro el alcance o puedes afectar a terceros, detente. La divulgación responsable empieza por respetar límites, minimizar datos y usar el canal oficial.
