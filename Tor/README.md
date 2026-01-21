# 👻 Ghost Mode: Tor Identity Manager

**Ghost Mode** es una herramienta de terminal escrita en Bash para gestionar el servicio Tor de forma ágil en sistemas Linux. Permite iniciar/detener el servicio, rotar la identidad (IP) y verificar la ubicación actual a través de `proxychains` con un dashboard visual limpio.

![Ghost Mode Dashboard](https://via.placeholder.com/800x400?text=Insertar+Captura+de+Pantalla+Aqui)
*(Recomendado: Sube una de tus capturas aquí para que se vea la tabla)*

## 🚀 Características

* **Gestión de Servicio:** Inicia y detiene el daemon de Tor (`systemctl`) automáticamente.
* **Rotación de Identidad:** Fuerza la renovación del circuito Tor (Signal HUP) para obtener una nueva IP sin reiniciar el servicio.
* **Verificación Visual:** Muestra una "Tarjeta de Identidad" con IP, País, Ciudad e ISP usando `jq` para un formato limpio.
* **Integración:** Diseñado para trabajar nativamente con `proxychains`.

---

## 🛠️ Instalación y Requisitos

Este script no requiere librerías de Python. Solo necesita paquetes estándar de sistema.

### 1. Clonar el Repositorio

```bash
git clone [https://github.com/TU_USUARIO/ghost-mode.sh.git](https://github.com/TU_USUARIO/ghost-mode.sh.git)
cd ghost-mode.sh
