# 🛡️ DNS Inspector Pro

**DNS Inspector Pro** es una herramienta de auditoría de alta precisión diseñada para verificar la integridad de los registros nominales (NS) en tiempo real. Utiliza un enfoque desacoplado y tipado para consultar múltiples proveedores DNS de confianza simultáneamente.

## 🚀 Características Principales

* **Arquitectura Orientada a Objetos:** Implementación basada en patrones de diseño para facilitar la extensibilidad.
* **Auditoría Multi-Proveedor:** Compara resultados entre Google DNS (`8.8.8.8`) y Cloudflare DNS (`1.1.1.1`).
* **Tipado Estricto:** Uso de `Type Hints` en todo el motor para asegurar la integridad de los datos.
* **Lógica Transversal:** Incorpora decoradores para la gestión de logs sin ensuciar la lógica de negocio.

## 🛠️ Requisitos Técnicos

* **Python:** 3.8 o superior.
* **Binarios de Sistema:** Requiere el comando `dig` disponible en el `PATH`.

## 📦 Instalación y Uso

1. Guarda el script como `dns.py`.
2. Ejecuta el motor desde la terminal:
   ```bash
   python3 dns.py