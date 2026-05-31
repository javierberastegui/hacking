# Guía para redactar evidencias sin exponer datos sensibles

La evidencia en un reporte de responsible disclosure debe ayudar al equipo responsable a entender el problema sin aumentar el daño. Menos datos, mejor redactados, suelen ser más seguros que capturas completas.

## Qué ocultar siempre

- Datos de acceso, material de sesión, llaves de servicio y cabeceras de autorización.
- Códigos OTP, enlaces mágicos, enlaces de restablecimiento o claves de recuperación.
- Correos, teléfonos, direcciones, nombres reales, documentos de identidad y datos de terceros.
- IDs internos si permiten consultar recursos ajenos.
- Mensajes privados, historiales, facturas, expedientes, documentos o datos financieros.
- Rutas internas, logs completos o configuraciones que revelen datos sensibles.

## Cómo redactar

- Sustituye datos reales por ejemplos: `usuario@example.invalid`, `ID-REDACTADO`, `DATO-OCULTO`.
- Recorta capturas para mostrar solo la zona necesaria.
- Difumina o tapa datos antes de compartir; no confíes en ocultaciones reversibles.
- Mantén la fecha, contexto y resultado observado si son necesarios para reproducir internamente.
- Explica qué eliminaste: “captura redactada para ocultar datos personales”.

## Qué evitar en los pasos

- Payloads exactos o cadenas que permitan reproducir abuso directamente.
- Automatización, scripts, fuzzing, scraping o enumeración.
- Instrucciones para saltar controles, persistir acceso o ampliar impacto.
- Pruebas sobre activos no incluidos en la política.

## Ejemplo seguro de redacción

En lugar de:

> Al cambiar el parámetro exacto `...` pude ver el documento completo de otra persona con nombre, DNI y dirección.

Usa:

> En una cuenta propia de prueba observé que una sección parecía devolver un recurso que no correspondía al usuario autenticado. Adjunto captura redactada con identificadores ficticios para que el equipo pueda revisarlo sin exponer datos de terceros.

## Recordatorio

Si la evidencia mínima sigue exponiendo datos sensibles o dudas legales, detente y pide instrucciones por el canal oficial antes de enviar más información.
