# -*- coding: utf-8 -*-
# runtime.py
# Entorno de ejecucion polimorfico para BrickScript (Soporte completo: TANKS, SNAKE, TETRIS)
# Uso: python runtime.py <archivo_juego.json>

import sys
import json
import time

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

# Generador Pseudoaleatorio Congruencial Lineal
class PRNG(object):
    def __init__(self):
        self.state = int(time.time() * 1000000) & 0x7FFFFFFF

    def _next(self):
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return self.state

    def random(self):
        return float(self._next()) / 2147483648.0

    def randint(self, a, b):
        if a > b:
            a, b = b, a
        return a + int(self.random() * (b - a + 1))

    def choice(self, lst):
        if not lst:
            return None
        idx = int(self.random() * len(lst))
        return lst[min(idx, len(lst) - 1)]

prng = PRNG()

class BrickRuntime(object):
    def __init__(self, json_path):
        with open(json_path, 'r') as f:
            self.ast = json.load(f)

        self.game_type = self.ast.get("game_type", "TANKS")
        self.grid_w = self.ast["grid"][0]
        self.grid_h = self.ast["grid"][1]
        self.cell_size = 25
        self.speed = self.ast.get("initial_speed", 150)

        self.root = tk.Tk()
        self.root.title("BrickScript Engine - " + str(self.game_type))
        self.root.resizable(False, False)

        canvas_w = self.grid_w * self.cell_size
        canvas_h = self.grid_h * self.cell_size

        self.canvas = tk.Canvas(self.root, width=canvas_w, height=canvas_h, bg="#111111")
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        self.sidebar = tk.Frame(self.root, width=180, bg="#222222")
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.lbl_title = tk.Label(self.sidebar, text=str(self.game_type), font=("Consolas", 16, "bold"), fg="#FFFFFF", bg="#222222")
        self.lbl_title.pack(pady=10)

        self.score = 0
        self.lbl_score_title = tk.Label(self.sidebar, text="PUNTUACION", font=("Consolas", 12), fg="#AAAAAA", bg="#222222")
        self.lbl_score_title.pack()
        self.lbl_score = tk.Label(self.sidebar, text="0", font=("Consolas", 18, "bold"), fg="#00FF00", bg="#222222")
        self.lbl_score.pack(pady=5)

        self.lbl_info = tk.Label(self.sidebar, text="", font=("Consolas", 10), fg="#FFFF00", bg="#222222", justify=tk.LEFT)
        self.lbl_info.pack(pady=10)

        self.game_over = False
        self.victory = False
        self.tick_count = 0

        if self.game_type == "TANKS":
            self.init_tanks()
        elif self.game_type == "SNAKE":
            self.init_snake()
        elif self.game_type == "TETRIS":
            self.init_tetris()

        self.bind_controls()
        self.ejecutar_evento("START")
        self.root.after(self.speed, self.game_loop)

    def bind_controls(self):
        self.root.bind("<Up>", lambda e: self.ejecutar_evento("KEY_UP"))
        self.root.bind("<Down>", lambda e: self.ejecutar_evento("KEY_DOWN"))
        self.root.bind("<Left>", lambda e: self.ejecutar_evento("KEY_LEFT"))
        self.root.bind("<Right>", lambda e: self.ejecutar_evento("KEY_RIGHT"))
        self.root.bind("<space>", lambda e: self.ejecutar_evento("KEY_SPACE"))

    # --- MOTOR TANQUES ---
    def init_tanks(self):
        self.player_x = 10
        self.player_y = 18
        self.player_dir = (0, -1)
        self.player_hp = 3
        
        shapes = self.ast.get("shapes", {})
        if "PLAYER_TANK" in shapes:
            self.player_hp = shapes["PLAYER_TANK"].get("hp", 3)

        self.bullets = []
        self.enemies = []
        self.boss = None
        self.boss_hp = 0
        self.boss_spawned = False
        self.boss_dir = 1

        self.obstacles = []
        muros_coords = [
            (3, 14), (4, 14), (5, 14),
            (14, 14), (15, 14), (16, 14),
            (3, 8), (4, 8), (15, 8), (16, 8),
            (8, 10), (9, 10), (10, 10), (11, 10)
        ]
        for ox, oy in muros_coords:
            self.obstacles.append({"x": ox, "y": oy, "hp": 2})

        self.spawn_enemy()
        self.spawn_enemy()

    def spawn_enemy(self):
        ex = prng.randint(1, self.grid_w - 2)
        ey = prng.randint(1, 4)
        if not self.is_occupied_cell(ex, ey):
            self.enemies.append({"x": ex, "y": ey, "hp": 1, "dir": (0, 1), "color": "#FF0000"})

    def is_occupied_cell(self, x, y, ignore_player=False):
        if not (0 <= x < self.grid_w and 0 <= y < self.grid_h):
            return True
        for obs in self.obstacles:
            if obs["x"] == x and obs["y"] == y:
                return True
        if not ignore_player and x == self.player_x and y == self.player_y:
            return True
        for e in self.enemies:
            if e["x"] == x and e["y"] == y:
                return True
        if self.boss and self.boss_hp > 0:
            bx, by = self.boss["x"], self.boss["y"]
            if bx <= x < bx + 3 and by <= y < by + 3:
                return True
        return False

    # --- MOTOR SNAKE ---
    def init_snake(self):
        self.snake_body = [(self.grid_w // 2, self.grid_h // 2)]
        self.snake_dir = (0, -1)
        self.food = self.obtener_coordenada_vacia()
        
        self.has_poison = self.ast.get("has_poison", False)
        self.poison_food = None
        self.powerup_food = None
        if self.has_poison:
            self.spawn_poison_food()

        self.snake_obstacles = []
        self.cargar_mapa_nivel("1") # Carga inicial limpia

    def cargar_mapa_nivel(self, nivel_str):
        """Carga los muros (#) de un nivel específico en Snake"""
        self.snake_obstacles = []
        levels = self.ast.get("levels", {})
        if nivel_str in levels and "map" in levels[nivel_str]:
            mapa = levels[nivel_str]["map"]
            for r_idx, row in enumerate(mapa):
                for c_idx, cell in enumerate(row):
                    if cell == '#':
                        self.snake_obstacles.append((c_idx, r_idx))

    def spawn_poison_food(self):
        px = prng.randint(0, self.grid_w - 1)
        py = prng.randint(0, self.grid_h - 1)
        if (px, py) not in self.snake_body and (px, py) != self.food:
            self.poison_food = (px, py)

    def obtener_coordenada_vacia(self):
        """Busca una coordenada que no choque con nada en el mapa de Snake"""
        while True:
            px = prng.randint(0, self.grid_w - 1)
            py = prng.randint(0, self.grid_h - 1)
            pos = (px, py)
            
            # 1. No debe estar sobre la serpiente ni en los muros
            if pos in getattr(self, 'snake_body', []) or pos in getattr(self, 'snake_obstacles', []):
                continue
                
            # 2. No debe sobreponerse a otras frutas existentes
            if getattr(self, 'food', None) == pos: continue
            if getattr(self, 'poison_food', None) == pos: continue
            if getattr(self, 'powerup_food', None) == pos: continue
            
            return pos

    # --- MOTOR TETRIS ---
    def init_tetris(self):
        self.grid = [[None for _ in range(self.grid_w)] for _ in range(self.grid_h)]
        self.curr_shape_name = None
        self.curr_piece = None
        self.curr_states = []
        self.curr_state_idx = 0
        self.curr_color = "#00FFFF"
        self.curr_x = 0
        self.curr_y = 0
        self.spawn_tetris_piece()

    def spawn_tetris_piece(self):
        shapes = self.ast.get("shapes", {})
        if not shapes:
            shapes = {"DEFAULT": {"color": "#00FFFF", "chance": 1.0, "states": [[[1, 1], [1, 1]]]}}
        
        shape_names = list(shapes.keys())
        chances = [shapes[name].get("chance", 1.0) for name in shape_names]
        total_chance = sum(chances)
        
        if total_chance > 0:
            r = prng.random() * total_chance
            accum = 0.0
            chosen = shape_names[0]
            for name, ch in zip(shape_names, chances):
                accum += ch
                if r <= accum:
                    chosen = name
                    break
            self.curr_shape_name = chosen
        else:
            self.curr_shape_name = prng.choice(shape_names)

        shape_data = shapes[self.curr_shape_name]
        self.curr_color = shape_data.get("color", "#00FFFF")
        states = shape_data.get("states", [])
        if not states:
            states = [[[1, 1], [1, 1]]]
        
        self.curr_states = states
        self.curr_state_idx = 0
        self.curr_piece = self.curr_states[0]
        
        pw = len(self.curr_piece[0]) if self.curr_piece else 2
        self.curr_x = (self.grid_w - pw) // 2
        self.curr_y = 0

        if not self.valid_tetris_pos(self.curr_piece, self.curr_x, self.curr_y):
            self.game_over = True

    def valid_tetris_pos(self, piece, px, py):
        for r_idx, row in enumerate(piece):
            for c_idx, val in enumerate(row):
                if val:
                    gx = px + c_idx
                    gy = py + r_idx
                    if gx < 0 or gx >= self.grid_w or gy < 0 or gy >= self.grid_h:
                        return False
                    if gy >= 0 and self.grid[gy][gx] is not None:
                        return False
        return True

    def tetris_move(self, dx, dy):
        if self.valid_tetris_pos(self.curr_piece, self.curr_x + dx, self.curr_y + dy):
            self.curr_x += dx
            self.curr_y += dy
            return True
        elif dy > 0:
            self.lock_tetris_piece()
            return False
        return False

    def tetris_rotate(self):
        if not self.curr_states:
            return
        next_idx = (self.curr_state_idx + 1) % len(self.curr_states)
        next_piece = self.curr_states[next_idx]
        if self.valid_tetris_pos(next_piece, self.curr_x, self.curr_y):
            self.curr_state_idx = next_idx
            self.curr_piece = next_piece

    def lock_tetris_piece(self):
        for r_idx, row in enumerate(self.curr_piece):
            for c_idx, val in enumerate(row):
                if val:
                    gx = self.curr_x + c_idx
                    gy = self.curr_y + r_idx
                    if 0 <= gy < self.grid_h and 0 <= gx < self.grid_w:
                        self.grid[gy][gx] = "#555555"

        lines_cleared = 0
        new_grid = []
        for row in self.grid:
            if all(cell is not None for cell in row):
                lines_cleared += 1
            else:
                new_grid.append(row)

        for _ in range(lines_cleared):
            new_grid.insert(0, [None for _ in range(self.grid_w)])

        self.grid = new_grid
        if lines_cleared > 0:
            self.score += lines_cleared * 100
            self.ejecutar_evento("LINE_CLEAR")

        # --- Lógica original restaurada para el Power-Up ---
        if lines_cleared >= 3 and "POWERUP" in self.ast.get("shapes", {}):
            self.curr_shape_name = "POWERUP"
            shape_data = self.ast["shapes"]["POWERUP"]
            self.curr_color = shape_data.get("color", "#FFFFFF")
            self.curr_states = shape_data.get("states", [[[1]]])
            self.curr_state_idx = 0
            self.curr_piece = self.curr_states[0]
            
            pw = len(self.curr_piece[0])
            self.curr_x = (self.grid_w - pw) // 2
            self.curr_y = 0
        else:
            self.spawn_tetris_piece()

    # --- EJECUTOR DE EVENTOS AST ---
    def ejecutar_evento(self, nombre_evento):
        if self.game_over or self.victory:
            return

        eventos = self.ast.get("events", {})
        acciones = eventos.get(nombre_evento, [])

        for acc in acciones:
            tipo = acc.get("type")
            target = acc.get("target")

            if tipo == "SPAWN":
                params = acc.get("params")

                # --- NUEVA LÓGICA DE SPAWN PARA SNAKE ---
                if target == "FOOD":
                    self.food = self.obtener_coordenada_vacia()
                elif target == "POISON_FRUIT":
                    self.poison_food = self.obtener_coordenada_vacia()
                elif target == "POWERUP":
                    self.powerup_food = self.obtener_coordenada_vacia()

                # --- NUEVA LÓGICA PARA FORZAR PIEZAS EN TETRIS ---
                if self.game_type == "TETRIS" and target in self.ast.get("shapes", {}):
                    self.curr_shape_name = target
                    shape_data = self.ast["shapes"][target]
                    self.curr_color = shape_data.get("color", "#FFFFFF")
                    self.curr_states = shape_data.get("states", [[[1]]])
                    self.curr_state_idx = 0
                    self.curr_piece = self.curr_states[0]
                    pw = len(self.curr_piece[0]) if self.curr_piece else 1
                    self.curr_x = (self.grid_w - pw) // 2
                    self.curr_y = 0
                    continue # Saltamos el resto de spawns

                if target == "PLAYER_TANK" and isinstance(params, list):
                    self.player_x, self.player_y = params[0]
                elif target in ["MEGA_FORTRESS", "BOSS"]:
                    boss_info = self.ast.get("boss", {})
                    bx = params[0][0] if isinstance(params, list) else 8
                    by = params[0][1] if isinstance(params, list) else 2
                    self.boss = {"x": bx, "y": by}
                    self.boss_hp = boss_info.get("hp", 15)
                    self.boss_spawned = True

            elif tipo == "CHANGE_DIRECTION" or tipo == "SET_DIRECTION":
                direccion = acc.get("direction")
                if self.game_type == "SNAKE":
                    if direccion == "UP" and self.snake_dir != (0, 1): self.snake_dir = (0, -1)
                    elif direccion == "DOWN" and self.snake_dir != (0, -1): self.snake_dir = (0, 1)
                    elif direccion == "LEFT" and self.snake_dir != (1, 0): self.snake_dir = (-1, 0)
                    elif direccion == "RIGHT" and self.snake_dir != (-1, 0): self.snake_dir = (1, 0)

            elif tipo == "MOVE":
                direccion = acc.get("direction")
                if target == "PLAYER_TANK":
                    nx, ny = self.player_x, self.player_y
                    if direccion == "UP": self.player_dir = (0, -1); ny -= 1
                    elif direccion == "DOWN": self.player_dir = (0, 1); ny += 1
                    elif direccion == "LEFT": self.player_dir = (-1, 0); nx -= 1
                    elif direccion == "RIGHT": self.player_dir = (1, 0); nx += 1

                    if not self.is_occupied_cell(nx, ny, ignore_player=True):
                        self.player_x, self.player_y = nx, ny

                elif target == "CURRENT_PIECE" or self.game_type == "TETRIS":
                    if direccion == "LEFT": self.tetris_move(-1, 0)
                    elif direccion == "RIGHT": self.tetris_move(1, 0)
                    # CORRECCIÓN: Evitamos que el evento "TICK" del archivo .brick force la caída
                    elif direccion == "DOWN" and nombre_evento != "TICK": 
                        self.tetris_move(0, 1)

            elif tipo == "ROTATE":
                if self.game_type == "TETRIS":
                    self.tetris_rotate()

            elif tipo == "SHOOT":
                if target == "PLAYER_TANK":
                    self.bullets.append({"x": self.player_x, "y": self.player_y, "dir": self.player_dir, "owner": "PLAYER"})

            elif tipo == "INCREASE_SCORE":
                self.score += acc.get("value", 0)
                self.lbl_score.config(text=str(self.score))

            elif tipo == "GROW":
                if self.game_type == "SNAKE" and self.snake_body:
                    # 1. Crecimiento estándar (Añade 1 bloque a la cola)
                    self.snake_body.append(self.snake_body[-1])
                    
                    # 2. Mecánica Especial Nyan Cat: Crecimiento acelerado
                    nivel_actual = self.ast.get("current_level", 1)
                    if nivel_actual >= 3:
                        # Añade un segundo bloque extra instantáneamente
                        self.snake_body.append(self.snake_body[-1])

            elif tipo == "INCREASE_SPEED":
                incremento = self.ast.get("speed_increment", 5)
                # Ponemos un freno distinto según el tipo de juego
                limite = 150 if self.game_type == "SNAKE" else 30
                self.speed = max(limite, self.speed - incremento)

            elif tipo == "NEXT_LEVEL":
                nivel_actual = self.ast.get("current_level", 1)
                nuevo_nivel = nivel_actual + 1
                self.ast["current_level"] = nuevo_nivel
                self.cargar_mapa_nivel(str(nuevo_nivel)) # <--- Llama al nuevo mapa
                
            elif tipo == "RESET_SNAKE":
                self.snake_body = [(self.grid_w // 2, self.grid_h // 2)]
                self.snake_dir = (0, -1)

        # Forzamos una actualizacion visual inmediata SOLO si el evento fue accionado por el jugador 
        # (ignoramos "TICK" para no redibujar doble en el bucle automatico)
        if nombre_evento != "TICK":
            self.render()

    # --- BUCLE Y LOGICA DE JUEGO ---
    def game_loop(self):
        if self.game_over:
            self.draw_game_over()
            return
        if self.victory:
            self.draw_victory()
            return

        self.tick_count += 1
        self.ejecutar_evento("TICK")

        if self.game_type == "TANKS":
            if self.tick_count % 5 == 0:
                for e in self.enemies:
                    opciones_dir = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                    if prng.random() < 0.6:
                        if abs(e["x"] - self.player_x) > abs(e["y"] - self.player_y):
                            e["dir"] = (1, 0) if e["x"] < self.player_x else (-1, 0)
                        else:
                            e["dir"] = (0, 1) if e["y"] < self.player_y else (0, -1)
                    elif prng.random() < 0.2:
                        e["dir"] = prng.choice(opciones_dir)

                    nx = e["x"] + e["dir"][0]
                    ny = e["y"] + e["dir"][1]
                    if not self.is_occupied_cell(nx, ny):
                        e["x"], e["y"] = nx, ny

            if self.tick_count % 2 == 0:
                for e in self.enemies:
                    mira_al_jugador = False
                    dx, dy = e["dir"]
                    if dx == 1 and dy == 0 and e["y"] == self.player_y and e["x"] < self.player_x: mira_al_jugador = True
                    elif dx == -1 and dy == 0 and e["y"] == self.player_y and e["x"] > self.player_x: mira_al_jugador = True
                    elif dx == 0 and dy == 1 and e["x"] == self.player_x and e["y"] < self.player_y: mira_al_jugador = True
                    elif dx == 0 and dy == -1 and e["x"] == self.player_x and e["y"] > self.player_y: mira_al_jugador = True

                    if mira_al_jugador and prng.random() < 0.8:
                        self.bullets.append({"x": e["x"], "y": e["y"], "dir": e["dir"], "owner": "ENEMY"})

            if self.boss and self.boss_hp > 0 and self.tick_count % 4 == 0:
                bx, by = self.boss["x"], self.boss["y"]
                nbx = bx + self.boss_dir
                if nbx <= 1 or nbx + 3 >= self.grid_w - 1:
                    self.boss_dir *= -1
                else:
                    self.boss["x"] = nbx

                if self.boss["x"] <= self.player_x < self.boss["x"] + 3 and self.boss["y"] <= self.player_y < self.boss["y"] + 3:
                    self.player_hp -= 1
                    if self.player_hp <= 0:
                        self.game_over = True

                if prng.random() < 0.30:
                    cx = self.boss["x"] + 1
                    cy = by + 2
                    self.bullets.append({"x": cx, "y": cy, "dir": (0, 1), "owner": "ENEMY"})
                    self.bullets.append({"x": cx, "y": cy, "dir": (-1, 1), "owner": "ENEMY"})
                    self.bullets.append({"x": cx, "y": cy, "dir": (1, 1), "owner": "ENEMY"})

            nuevas_balas = []
            for b in self.bullets:
                nx = b["x"] + b["dir"][0]
                ny = b["y"] + b["dir"][1]

                if not (0 <= nx < self.grid_w and 0 <= ny < self.grid_h):
                    continue

                impacto = False
                for obs in list(self.obstacles):
                    if obs["x"] == nx and obs["y"] == ny:
                        obs["hp"] -= 1
                        impacto = True
                        if obs["hp"] <= 0:
                            self.obstacles.remove(obs)
                        break

                if not impacto:
                    if b["owner"] == "PLAYER":
                        for e in list(self.enemies):
                            # --- NUEVO: Verificamos tanto la celda destino como la celda origen ---
                            if (e["x"] == nx and e["y"] == ny) or (e["x"] == b["x"] and e["y"] == b["y"]):
                                e["hp"] -= 1
                                impacto = True
                                if e["hp"] <= 0:
                                    self.enemies.remove(e)
                                    self.score += 100
                                break

                        if self.boss and self.boss_hp > 0 and not impacto:
                            bx, by = self.boss["x"], self.boss["y"]
                            # --- NUEVO: Doble chequeo para el jefe ---
                            if (bx <= nx < bx + 3 and by <= ny < by + 3) or (bx <= b["x"] < bx + 3 and by <= b["y"] < by + 3):
                                self.boss_hp -= 1
                                impacto = True
                                if self.boss_hp <= 0:
                                    self.score += 1000
                                    self.victory = True

                    elif b["owner"] == "ENEMY":
                        # --- NUEVO: Doble chequeo para el jugador ---
                        if (nx == self.player_x and ny == self.player_y) or (b["x"] == self.player_x and b["y"] == self.player_y):
                            self.player_hp -= 1
                            impacto = True
                            if self.player_hp <= 0:
                                self.game_over = True

                if not impacto:
                    b["x"], b["y"] = nx, ny
                    nuevas_balas.append(b)

            self.bullets = nuevas_balas

            if prng.random() < 0.08 and len(self.enemies) < 3:
                self.spawn_enemy()

            if self.score >= 1000 and not self.boss_spawned:
                self.ejecutar_evento("TARGET_SCORE_1000")

            self.lbl_score.config(text=str(self.score))

        elif self.game_type == "SNAKE":
            # 1. Apagar invulnerabilidad si se acabó el tiempo
            if getattr(self, 'invulnerable', False) and self.tick_count > getattr(self, 'invulnerability_end_tick', 0):
                self.invulnerable = False

            # --- NUEVO: Validacion de seguridad para evitar que el juego colapse ---
            if len(self.snake_body) == 0:
                return

            head_x, head_y = self.snake_body[0]
            new_head = (head_x + self.snake_dir[0], head_y + self.snake_dir[1])

            # Choques letales (Paredes o cuerpo)
            if not (0 <= new_head[0] < self.grid_w and 0 <= new_head[1] < self.grid_h) or new_head in self.snake_body or new_head in getattr(self, 'snake_obstacles', []):
                if not getattr(self, 'invulnerable', False):
                    self.game_over = True
            
            # Veneno (-50 puntos, -1 cola)
            elif getattr(self, 'poison_food', None) and new_head == self.poison_food:
                self.snake_body.insert(0, new_head) # Nos movemos al cuadro
                
                if not getattr(self, 'invulnerable', False):
                    # Penalización de Puntos
                    self.score = max(0, self.score - 50) 
                    self.lbl_score.config(text=str(self.score))
                    
                    # Penalización de Cola
                    self.snake_body.pop() # El pop() normal para avanzar
                    if len(self.snake_body) > 1:
                        self.snake_body.pop() # Segundo pop() para amputar una sección extra
                else:
                    self.snake_body.pop() # Si es invulnerable, solo avanza sin perder nada
                
                self.poison_food = None
                self.ejecutar_evento("EAT_POISON") # Delega al script la orden de spawnear más veneno
                
            # Power-up (Escudo Temporal)
            elif getattr(self, 'powerup_food', None) and new_head == self.powerup_food:
                self.invulnerable = True
                
                # Traducimos los 6 segundos de tu script a "ticks" del motor
                tiempo_seg = self.ast.get("invulnerability_time", 6)
                ticks_para_esperar = int(tiempo_seg * (1000 / max(self.speed, 1)))
                self.invulnerability_end_tick = self.tick_count + ticks_para_esperar
                
                self.snake_body.insert(0, new_head)
                self.snake_body.pop() # No crecemos
                self.powerup_food = None
                self.ejecutar_evento("ACTIVATE_POWERUP") 
                
            # Movimiento normal / Comida normal
            else:
                # 1. Insertamos la nueva cabeza
                self.snake_body.insert(0, new_head)
                
                # 2. ÚNICO POP: Borramos siempre la cola para que el motor no la haga crecer solo.
                # (El comando GROW en snake.brick se encargará de añadir la cola si come).
                self.snake_body.pop() 
                
                # 3. Evaluamos qué pasó en esta nueva posición
                if new_head == self.food:
                    self.ejecutar_evento("EAT_FOOD") 
                    
                    # Comprobamos si superamos la meta del nivel tras comer
                    current_level_str = str(self.ast.get("current_level", 1))
                    levels = self.ast.get("levels", {})
                    if current_level_str in levels:
                        goal = levels[current_level_str].get("score_goal", 999)
                        if self.score >= goal:
                            self.ejecutar_evento("LEVEL_UP")
                else:
                    # ¡CUIDADO! Ya NO hay pop() aquí. 
                    # Solo comprobamos la meta del nivel en movimiento normal
                    current_level_str = str(self.ast.get("current_level", 1))
                    levels = self.ast.get("levels", {})
                    if current_level_str in levels:
                        goal = levels[current_level_str].get("score_goal", 999)
                        if self.score >= goal:
                            self.ejecutar_evento("LEVEL_UP")

        elif self.game_type == "TETRIS":
            # Calculamos dinámicamente cuántos ticks equivalen a ~800ms
            # Si speed es 20ms, esperará 40 ticks. Si es 150ms, esperará 5 ticks.
            ticks_para_bajar = max(1, 800 // max(self.speed, 1))
            
            if self.tick_count % ticks_para_bajar == 0:
                self.tetris_move(0, 1)
            self.lbl_score.config(text=str(self.score))

        self.render()
        self.root.after(self.speed, self.game_loop)

    # --- RENDERIZADO GRAFICO ---
    def render(self):
        self.canvas.delete("all")
        cs = self.cell_size

        info_txt = ""
        if self.game_type == "TANKS":
            info_txt += "HP Jugador: " + str(self.player_hp) + "\n"
            if self.boss_spawned and self.boss_hp > 0:
                info_txt += "BOSS HP: " + str(self.boss_hp) + "\n"
        elif self.game_type == "SNAKE":
            info_txt += "Modo: " + str(self.ast.get("difficulty_mode", "BABY")) + "\n"
        elif self.game_type == "TETRIS":
            info_txt += "Pieza: " + str(self.curr_shape_name) + "\n"
        self.lbl_info.config(text=info_txt)

        if self.game_type == "TANKS":
            for obs in self.obstacles:
                color_muro = "#8B4513" if obs["hp"] > 1 else "#CD853F"
                self.canvas.create_rectangle(obs["x"]*cs, obs["y"]*cs, (obs["x"]+1)*cs, (obs["y"]+1)*cs, fill=color_muro, outline="#000000")

            px, py = self.player_x, self.player_y
            self.canvas.create_rectangle(px*cs, py*cs, (px+1)*cs, (py+1)*cs, fill="#00FF00", outline="#FFFFFF")

            for e in self.enemies:
                self.canvas.create_rectangle(e["x"]*cs, e["y"]*cs, (e["x"]+1)*cs, (e["y"]+1)*cs, fill=e["color"], outline="#FFFFFF")

            if self.boss and self.boss_hp > 0:
                bx, by = self.boss["x"], self.boss["y"]
                boss_color = self.ast.get("boss", {}).get("color", "#FF00FF")
                self.canvas.create_rectangle(bx*cs, by*cs, (bx+3)*cs, (by+3)*cs, fill=boss_color, outline="#FFFFFF")

            for b in self.bullets:
                b_color = "#FFFF00" if b["owner"] == "PLAYER" else "#FF4500"
                self.canvas.create_oval(b["x"]*cs+cs/3, b["y"]*cs+cs/3, (b["x"]+1)*cs-cs/3, (b["y"]+1)*cs-cs/3, fill=b_color)

        elif self.game_type == "SNAKE":
            shape_style = self.ast.get("shape_type", "RECTANGLE")
            
            # --- NUEVA LÓGICA DE DIFICULTAD ---
            # Leemos el nivel numérico actual (1, 2, 3...)
            nivel_actual = self.ast.get("current_level", 1)
            
            # Asignamos el modo gráfico correspondiente al nivel
            if nivel_actual == 1:
                modo_actual = "BABY"
            elif nivel_actual == 2:
                modo_actual = "ENTUSIASTA"
            else:
                modo_actual = "NYAN_CAT" # Nivel 3 en adelante

            # 1. Cambiar el color de fondo si es Nyan Cat
            if modo_actual == "NYAN_CAT":
                self.canvas.config(bg="#003366") # Azul espacial profundo
            else:
                self.canvas.config(bg="#111111") # Gris oscuro por defecto

            # 2. Muros / Obstáculos
            for ox, oy in getattr(self, 'snake_obstacles', []):
                color_muro = "#FFFFFF" if modo_actual == "NYAN_CAT" else "#555555" # Muros blancos tipo estrellas para Nyan Cat
                self.canvas.create_rectangle(ox*cs, oy*cs, (ox+1)*cs, (oy+1)*cs, fill=color_muro, outline="#000000")

            # 3. Dibujar Serpiente
            for idx, (bx, by) in enumerate(self.snake_body):
                if modo_actual == "NYAN_CAT":
                    if idx == 0:
                        # CABEZA DEL GATO
                        # Oreja Izquierda
                        self.canvas.create_polygon(bx*cs, by*cs, bx*cs+cs/2, by*cs, bx*cs, by*cs+cs/2, fill="#888888", outline="#000000")
                        # Oreja Derecha
                        self.canvas.create_polygon((bx+1)*cs, by*cs, (bx+1)*cs-cs/2, by*cs, (bx+1)*cs, by*cs+cs/2, fill="#888888", outline="#000000")
                        # Cara (Círculo Gris)
                        self.canvas.create_oval(bx*cs, by*cs, (bx+1)*cs, (by+1)*cs, fill="#AAAAAA", outline="#000000")
                        # Ojos (Negros)
                        self.canvas.create_oval(bx*cs+cs/4, by*cs+cs/4, bx*cs+cs*0.4, by*cs+cs*0.45, fill="#000000")
                        self.canvas.create_oval(bx*cs+cs*0.6, by*cs+cs/4, bx*cs+cs*0.75, by*cs+cs*0.45, fill="#000000")
                    else:
                        # CUERPO DE ARCOÍRIS
                        colores_arcoiris = ["#FF0000", "#FF9900", "#FFFF00", "#33FF00", "#0099FF", "#6633FF"]
                        color_cuerpo = colores_arcoiris[idx % len(colores_arcoiris)]
                        self.canvas.create_rectangle(bx*cs, by*cs, (bx+1)*cs, (by+1)*cs, fill=color_cuerpo, outline="#FFFFFF")
                else:
                    # SERPIENTE NORMAL
                    color = "#00FF00"
                    if shape_style == "CIRCULAR":
                        self.canvas.create_oval(bx*cs, by*cs, (bx+1)*cs, (by+1)*cs, fill=color, outline="#000000")
                    else:
                        self.canvas.create_rectangle(bx*cs, by*cs, (bx+1)*cs, (by+1)*cs, fill=color, outline="#000000")
            # Fruta Base
            if self.food:
                fx, fy = self.food
                if shape_style == "CIRCULAR":
                    self.canvas.create_oval(fx*cs, fy*cs, (fx+1)*cs, (fy+1)*cs, fill="#FF0000", outline="#FFFFFF")
                else:
                    self.canvas.create_rectangle(fx*cs, fy*cs, (fx+1)*cs, (fy+1)*cs, fill="#FF0000", outline="#FFFFFF")

            # Fruta Venenosa (Siempre Triangular)
            if self.poison_food:
                px, py = self.poison_food
                self.canvas.create_polygon(
                    px*cs + cs/2, py*cs,         # Punta superior
                    px*cs, py*cs + cs,           # Esquina inferior izquierda
                    px*cs + cs, py*cs + cs,      # Esquina inferior derecha
                    fill="#A020F0", outline="#FFFFFF"
                )

            # Power-up (Escudo azul)
            if getattr(self, 'powerup_food', None):
                px, py = self.powerup_food
                self.canvas.create_rectangle(px*cs, py*cs, (px+1)*cs, (py+1)*cs, fill="#00FFFF", outline="#FFFFFF")

        elif self.game_type == "TETRIS":
            # 1. Dibujar el fondo y las piezas ya fijadas (grises)
            for r in range(self.grid_h):
                for c in range(self.grid_w):
                    color = self.grid[r][c]
                    if color:
                        self.canvas.create_rectangle(c*cs, r*cs, (c+1)*cs, (r+1)*cs, fill=color, outline="#000000")

            # 2. Dibujar la pieza actual viva que está cayendo (con su color original)
            if self.curr_piece:
                for r_idx, row in enumerate(self.curr_piece):
                    for c_idx, val in enumerate(row):
                        if val:
                            gx = (self.curr_x + c_idx) * cs
                            gy = (self.curr_y + r_idx) * cs
                            self.canvas.create_rectangle(gx, gy, gx+cs, gy+cs, fill=self.curr_color, outline="#FFFFFF")

    def draw_game_over(self):
        self.canvas.create_text(self.grid_w*self.cell_size//2, self.grid_h*self.cell_size//2, text="GAME OVER", font=("Consolas", 24, "bold"), fill="#FF0000")

    def draw_victory(self):
        self.canvas.create_text(self.grid_w*self.cell_size//2, self.grid_h*self.cell_size//2, text="VICTORIA!", font=("Consolas", 24, "bold"), fill="#00FF00")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python runtime.py <archivo_juego.json>")
        sys.exit(1)
    app = BrickRuntime(sys.argv[1])
    app.root.mainloop()