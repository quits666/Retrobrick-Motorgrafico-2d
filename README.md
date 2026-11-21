# BrickScript — Lenguaje de Dominio Específico (DSL) y Motor de Juegos Retro

🎥 **Video demostrativo:** [Ver demostración en YouTube](https://youtu.be/T-DsPtYfirU)

**BrickScript** es un Lenguaje de Dominio Específico (DSL) diseñado para crear y extender videojuegos clásicos estilo *Brick Game* (**Tetris**, **Snake** y **Tanks**). 

El proyecto integra un **compilador propio** en Python —basado en análisis léxico (*lexer*) y un **Árbol AVL** que traduce scripts `.brick` a configuraciones **JSON**— junto con un **motor gráfico 2D** basado en matrices encargado de ejecutar reglas, eventos y físicas en tiempo real.

---

## Cómo Jugar

1. Abre una terminal (`cmd.exe` o la terminal de VS Code) en la carpeta raíz del proyecto.
2. Ejecuta `jugar.bat` seguido del nombre del juego (sin la extensión `.brick`). El script compilará el código y lanzará el motor automáticamente:

```cmd
# Juegos originales
jugar.bat snake
jugar.bat tetris

# Nuevos juegos y versiones evolucionadas
jugar.bat snake_evolved
jugar.bat tetris_remake
jugar.bat tanks

> **Nota:** Presiona la tecla **q** en cualquier momento para salir del juego.
