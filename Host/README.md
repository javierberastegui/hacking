# 💀 Ephemeral CTF Hosts Manager



## 🎯 Propósito
Este no es el típico script que ensucia tu `/etc/hosts`. Es un gestor de estado efímero diseñado para inyectar objetivos (`IP -> Hostname`) de forma volátil durante sesiones de CTF o auditorías, garantizando una reversión atómica del sistema al finalizar.

## 🏗️ Arquitectura de Nivel Pro
La herramienta se aleja de la manipulación de strings crudos y adopta patrones de diseño avanzados para asegurar la integridad del sistema:

### 1. Gestión de Ciclo de Vida (Context Management)
Utiliza la clase `EphemeralHostsSession` como un **Context Manager** de Python. Esto garantiza que, pase lo que pase (incluso si el script crashea o lo detienes con `Ctrl+C`), el método `__exit__` se ejecute para limpiar las entradas inyectadas.

### 2. Abstracción de Datos
En lugar de tratar el archivo como un bloque de texto, se utiliza la dataclass `HostEntry`. Esto permite:
* **Idempotencia**: Si una IP ya existe, el script anexa el hostname en lugar de duplicar líneas.
* **Preservación**: Los comentarios y el formato original del archivo se respetan escrupulosamente.

### 3. Seguridad y Resiliencia
* **Decoradores de Privilegio**: Implementa `@require_root` para evitar fallos de escritura silenciosos.
* **Backups Automáticos**: Crea una copia `.bak` antes de cualquier modificación.

## 🔄 Flujo de Operación

| Fase | Acción | Resultado |
| :--- | :--- | :--- |
| **Setup** | `_backup()` & `_load_entries()` | El estado original se congela y se mapea a memoria. |
| **Injection** | `add_target(ip, host)` | Se actualiza el modelo y se hace un `_flush()` inmediato al disco. |
| **Teardown** | `_cleanup_session_data()` | Se identifican y revocan **únicamente** las entradas creadas en la sesión actual. |

## 🚀 Uso Rápido
1. Ejecuta con `sudo python ctf_hosts.py`.
2. Define tu IP objetivo una sola vez.
3. Inyecta hostnames de forma continua (ej. `vhost1.htb`, `vhost2.htb`).
4. Sal con `:exit` y observa cómo el archivo `/etc/hosts` vuelve a su estado original mágicamente.
