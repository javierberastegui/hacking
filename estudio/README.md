# 🍅 ArchitectFocus CLI v2.0

> **A High-Performance, Over-Engineered Pomodoro Timer for Python Purists.**

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)
![Architecture](https://img.shields.io/badge/architecture-solid-orange)

## 📖 Overview

**ArchitectFocus** is not your average productivity script. It is a robust, scalable, and type-strict Command Line Interface (CLI) designed to manage temporal cycles (Pomodoro technique) with architectural elegance.

Instead of relying on simple loops and blocking calls, this project demonstrates advanced Python patterns to handle state, resources, and user feedback efficiently.

## 🛠️ Technical Arsenal

This project was built to showcase **Senior-level Python capabilities**:

* **Context Managers (`__enter__`, `__exit__`)**: Ensures fail-safe resource management and clean session teardowns, even during forced interruptions.
* **Generators & Yield**: Implements memory-efficient time tracking that yields control rather than blocking execution flow.
* **Closures & Factory Patterns**: Encapsulates state for notification and motivation systems, avoiding global variables and tightly coupled logic.
* **Decorators**: Handles cross-cutting concerns (logging/auditing) without polluting business logic.
* **Dataclasses (Frozen)**: Guarantees configuration immutability and thread-safety potential.
* **Strict Typing**: 100% Type Hint coverage for predictability and IDE support.

## 🚀 Installation

No heavy dependencies. Just pure, standard-library Python power.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/architect-focus-cli.git](https://github.com/your-username/architect-focus-cli.git)
    cd architect-focus-cli
    ```

2.  **Run the system:**
    ```bash
    python main.py
    ```

## ⚙️ Configuration

The system is configured via the `PomodoroConfig` dataclass, ensuring a single source of truth:

```python
@dataclass(frozen=True)
class PomodoroConfig:
    focus_duration: int = 25  # Minutes
    break_duration: int = 5   # Minutes
    cycles: int = 4
