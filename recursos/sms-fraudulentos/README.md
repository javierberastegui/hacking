# Recurso defensivo: SMS fraudulentos (smishing)

Recurso público y local para acompañar el artículo:

- Artículo: https://javierberastegui.es/como-detectar-sms-fraudulentos
- Tema: cómo detectar SMS fraudulentos, documentar lo ocurrido y actuar por canales oficiales.

## Propósito

Esta carpeta reúne una checklist, una plantilla manual y un pequeño helper local para ayudar a lectores generales a ordenar la información tras recibir un SMS sospechoso.

El objetivo no es investigar al atacante ni comprobar enlaces, sino reducir el riesgo de actuar con prisas: cortar la interacción con el mensaje, conservar datos básicos y verificar cualquier incidencia por canales oficiales independientes del SMS.

## Contenido

- `generar_registro_sms.py`: script local que genera una plantilla Markdown de registro del incidente a partir de campos manuales opcionales.
- `checklist_respuesta_smishing.md`: checklist defensiva de respuesta ante SMS sospechosos.
- `plantilla_registro_sms_sospechoso.md`: plantilla manual para copiar, imprimir o completar en una nota local.

## Límites de seguridad

Este recurso es exclusivamente defensivo y local.

No hace ni debe hacer lo siguiente:

- abrir enlaces del SMS;
- validar dominios;
- escanear, rastrear o analizar infraestructura de terceros;
- contactar con servicios externos;
- enviar datos a ninguna API;
- crear plantillas de phishing;
- automatizar mensajes;
- recolectar credenciales;
- evadir filtros o controles;
- sustituir al banco, operador, policía, asesoramiento jurídico o soporte técnico especializado.

## Uso rápido

Mostrar ayuda:

```bash
python3 recursos/sms-fraudulentos/generar_registro_sms.py --help
```

Imprimir una plantilla vacía por pantalla:

```bash
python3 recursos/sms-fraudulentos/generar_registro_sms.py
```

Crear un registro local con datos de ejemplo seguros:

```bash
python3 recursos/sms-fraudulentos/generar_registro_sms.py \
  --fecha "2026-05-28 10:30" \
  --remitente "Aviso" \
  --entidad "Empresa de paquetería" \
  --resumen "SMS que indica una supuesta entrega pendiente" \
  --enlace-visible "ejemplo.invalid/aviso" \
  --accion-solicitada "Pagar una tasa" \
  --click "No" \
  --datos "No" \
  --output /tmp/registro_sms_demo.md
```

Nota: `ejemplo.invalid` es un dominio reservado para documentación. No se abre ni se consulta.

## Flujo recomendado

1. No respondas al SMS.
2. No abras enlaces ni llames a números incluidos en el mensaje.
3. Copia solo la información visible que ya tengas delante, sin interactuar más.
4. Completa la plantilla local o imprime el documento.
5. Verifica cualquier incidencia desde la app oficial, web escrita manualmente, teléfono de la tarjeta/factura/contrato o soporte verificado.
6. Si introdujiste credenciales, datos bancarios, códigos OTP o autorizaste un pago, contacta cuanto antes con la entidad afectada por canales oficiales.

## Aviso

Estas señales y pasos no prueban por sí solos que un SMS sea fraudulento y no garantizan recuperar dinero ni evitar cualquier daño. Sirven para organizar la respuesta, conservar información útil y evitar nuevas interacciones con el mensaje sospechoso.
