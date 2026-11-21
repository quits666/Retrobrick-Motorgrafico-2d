=============================================================
          PROYECTO: BrickScript - Un Lenguaje para Juegos Retro
=============================================================

Link video demostrativo: https://youtu.be/T-DsPtYfirU

BrickScript es un lenguaje de programacion simple (un "DSL" o Lenguaje de Dominio Especifico) disenado para crear juegos clasicos de estilo "Brick Game", como Tetris y Snake.

Este proyecto incluye el compilador que traduce el codigo BrickScript a un formato que la computadora entiende, y el motor de juego que lo ejecuta.

-------------------------------------------------------------
                      COMO JUGAR
-------------------------------------------------------------

Para compilar y ejecutar un juego, hemos creado un script que hace todo el trabajo por ti.

1. Abre una terminal de comandos (cmd.exe) en la carpeta principal del proyecto.
2. Usa el comando "jugar.bat" seguido del nombre del juego que quieres ejecutar (sin la extension .brick).

   JUEGOS ORIGINALES:
   jugar.bat snake
   jugar.bat tetris

   NUEVOS JUEGOS Y VERSIONES EVOLUCIONADAS:
   jugar.bat snake_evolved
   jugar.bat tetris_remake
   jugar.bat tanks

El script primero compilara el archivo .brick correspondiente. Si la compilacion es exitosa, el juego se iniciara automaticamente.
Para salir del juego, presiona la tecla 'q'.

-------------------------------------------------------------
                 SINTAXIS DE BRICKSCRIPT (ORIGINAL Y EXTENDIDA)
-------------------------------------------------------------

El lenguaje se basa en bloques de comandos simples y faciles de entender.

--- COMANDOS GENERALES (BASE) ---
* GAME_TYPE [TIPO_DE_JUEGO]
    Define que logica usara el motor. Obligatorio. (Ej: TETRIS, SNAKE, TANKS)
* GAME_GRID (ANCHO, ALTO)
    Establece el tamano del area de juego.
* DEFINE SHAPE [NOMBRE_PIEZA]: ... END
    Define una forma geometrica con uno o mas estados.

--- ETIQUETAS AVANZADAS (NUEVO) ---
* COLOR [HEX]: Asigna un color a la pieza (Ej: COLOR #FF0000).
* CHANCE [DECIMAL]: Modifica la probabilidad de spawn (Ej: CHANCE 1.5).
* INITIAL_SPEED [NUM] / SPEED_INCREMENT [NUM]: Controlan la velocidad general del motor.
* LEVELS { LEVEL [TIPO]: ... }: Define dificultades y metas de puntaje.
* TYPE: [PLAYER | ENEMY | BULLET | POWERUP]: Categoriza entidades (Exclusivo de Tanks).
* HP [NUM] / SPEED [NUM] / HEALS [NUM]: Atributos de combate para entidades.
* DEFINE BOSS [NOMBRE]: ... END: Crea un jefe final con vida y comportamiento propio.

--- SINTAXIS PARA TETRIS ---
Eventos disponibles: ON START, ON TICK, ON LINE_CLEAR, ON KEY_UP, ON KEY_DOWN, ON KEY_LEFT, ON KEY_RIGHT
Acciones comunes: SPAWN RANDOM_SHAPE, MOVE CURRENT_PIEZA, ROTATE CURRENT_PIEZA, INCREASE_SCORE

--- SINTAXIS PARA SNAKE ---
Eventos disponibles: ON START, ON TICK, ON EAT_FOOD, ON EAT_POISON, ON HIT_CLOUD, ON COLLISION_WALL, ON COLLISION_SELF, ON KEY_...
Acciones comunes: SPAWN PLAYER/FOOD, MOVE PLAYER FORWARD, SET_DIRECTION, GROW PLAYER, START_INVULNERABILITY

--- SINTAXIS PARA TANKS (NUEVO) ---
Eventos disponibles: ON START, ON TICK, ON TARGET_SCORE, ON KEY_UP, ON KEY_DOWN, ON KEY_LEFT, ON KEY_RIGHT, ON KEY_SPACE
Acciones comunes: MOVE [ENTIDAD], SPAWN [ENTIDAD], SHOOT [ENTIDAD]