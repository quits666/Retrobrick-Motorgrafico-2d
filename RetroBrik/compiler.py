# -*- coding: utf-8 -*-
# compiler.py
# Compilador universal para BrickScript (Versión Polimórfica - Actividad 6)
# Uso: python compiler.py <archivo_entrada.brick>

import sys
import json

def lexer(codigo):
    tokens = []
    lineas = codigo.split('\n')
    
    for linea in lineas:
        linea_str = linea.strip()
        
        # 1. Ignorar lineas vacias o comentarios de linea completa
        if not linea_str or linea_str.startswith('#'):
            continue
            
        # 2. Ignorar comentarios de fin de linea
        linea_limpia = ""
        partes = linea.split()
        for p in partes:
            if p.startswith('#') and len(p) != 7 and p != '#':
                break
            linea_limpia += p + " "
            
        # 3. Extraer tokens de la linea limpia
        i = 0
        s = linea_limpia.strip()
        while i < len(s):
            if s[i].isspace():
                i += 1
                continue
            
            if s[i] in '(),:[]':
                tokens.append(s[i])
                i += 1
                continue
            
            inicio = i
            while i < len(s) and not s[i].isspace() and s[i] not in '(),:[]':
                i += 1
            tokens.append(s[inicio:i])

    return tokens


class Parser(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0
        self.ast = {
            "game_type": None,
            "grid": [20, 20],
            "initial_speed": 300,
            "speed_increment": 10,
            "shape_type": "RECTANGLE",  # Por defecto
            "difficulty_mode": "BABY",   # Por defecto
            "invulnerability_time": 0,
            "has_poison": False,
            "has_obstacles": False,
            "shapes": {},
            "levels": {},
            "events": {}
        }

    def consumir(self, token_esperado=None):
        if self.posicion < len(self.tokens):
            token_actual = self.tokens[self.posicion]
            if token_esperado and token_actual != token_esperado:
                raise Exception("Error de sintaxis: Se esperaba '" + str(token_esperado) + "' pero se encontro '" + str(token_actual) + "'")
            self.posicion += 1
            return token_actual
        else:
            raise Exception("Error de sintaxis: Fin de archivo inesperado")

    def parse(self):
        self.consumir('GAME_TYPE')
        self.ast['game_type'] = self.consumir()

        self.consumir('GAME_GRID')
        self.consumir('(')
        ancho = int(self.consumir())
        self.consumir(',')
        alto = int(self.consumir())
        self.consumir(')')
        self.ast['grid'] = [ancho, alto]

        # Parametros opcionales de velocidad
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] in ['INITIAL_SPEED', 'SPEED_INCREMENT']:
            token_config = self.consumir()
            if token_config == 'INITIAL_SPEED':
                self.ast['initial_speed'] = int(self.consumir())
            elif token_config == 'SPEED_INCREMENT':
                self.ast['speed_increment'] = int(self.consumir())

        # Bucle principal polimórfico
        while self.posicion < len(self.tokens):
            token_actual = self.tokens[self.posicion]

            if token_actual == 'LEVELS':
                self.parsear_bloque_levels()

            elif token_actual == 'DEFINE':
                self.consumir('DEFINE')
                tipo_def = self.consumir()
                if tipo_def == 'SHAPE':
                    if self.posicion < len(self.tokens) and self.tokens[self.posicion] in ['CIRCULAR', 'TRIANGULAR', 'RECTANGLE']:
                        self.ast['shape_type'] = self.consumir()
                    else:
                        self.parsear_shape_body(es_boss=False)
                elif tipo_def == 'BOSS':
                    self.parsear_shape_body(es_boss=True)
                elif tipo_def == 'LEVEL':
                    self.parsear_level_body()

            elif token_actual == 'ON':
                self.parsear_evento()

            else:
                self.posicion += 1

        return self.ast

    def parsear_bloque_levels(self):
        self.consumir('LEVELS') # <-- Línea añadida para procesar los LEVELS nuevos
        self.consumir('{')
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] != '}':
            token = self.tokens[self.posicion]
            
            if token == 'LEVEL':
                self.consumir('LEVEL')
                modo = self.consumir()  
                self.ast['difficulty_mode'] = modo
                if self.posicion < len(self.tokens) and self.tokens[self.posicion] == ':':
                    self.consumir(':')
            elif token == 'HAS_POISON_FRUIT':
                self.consumir('HAS_POISON_FRUIT')
                val = self.consumir()
                self.ast['has_poison'] = (val == 'TRUE')
            elif token == 'HAS_OBSTACLES':
                self.consumir('HAS_OBSTACLES')
                val = self.consumir()
                self.ast['has_obstacles'] = (val == 'TRUE')
            elif token == 'INVULNERABILITY_TIME':
                self.consumir('INVULNERABILITY_TIME')
                self.ast['invulnerability_time'] = int(self.consumir())
                if self.posicion < len(self.tokens) and self.tokens[self.posicion] == 'SECONDS':
                    self.consumir('SECONDS')
            elif token == 'SPEED':
                self.consumir('SPEED')
                velocidad_nivel = int(self.consumir())
                
                # Creamos un diccionario seguro para guardar las velocidades de cada modo
                # sin dañar la variable global 'initial_speed'
                if 'level_speeds' not in self.ast:
                    self.ast['level_speeds'] = {}
                self.ast['level_speeds'][modo] = velocidad_nivel
            else:
                self.consumir()
        self.consumir('}')

    def parsear_shape_body(self, es_boss):
        nombre_shape = self.consumir()
        
        # Propiedades base unificadas (Tetris, Tanks, Snake)
        propiedades = {
            "color": "#00FFFF",
            "chance": 1.0,
            "states": [],
            "type": "BOSS" if es_boss else "DEFAULT",
            "hp": 1,
            "speed": 1,
            "heals": 0
        }

        # Analizador de etiquetas flexible (Inline o Multilínea)
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] != 'STATE':
            token_attr = self.consumir()
            
            if token_attr == ':':
                continue
            elif token_attr == 'COLOR':
                propiedades["color"] = self.consumir()
            elif token_attr == 'CHANCE':
                propiedades["chance"] = float(self.consumir())
            elif token_attr == 'TYPE':
                if self.tokens[self.posicion] == ':':
                    self.consumir(':')
                propiedades["type"] = self.consumir()
            elif token_attr == 'HP':
                propiedades["hp"] = int(self.consumir())
            elif token_attr == 'SPEED':
                propiedades["speed"] = int(self.consumir())
            elif token_attr == 'HEALS':
                propiedades["heals"] = int(self.consumir())

        # Analizador de matrices flexible
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] == 'STATE':
            self.consumir('STATE')
            self.consumir() 
            if self.tokens[self.posicion] == ':':
                self.consumir(':')
            
            # Detectar si Tanks envolvió la matriz en un corchete extra STATE 1 [ [1,1] ]
            tiene_wrapper = False
            if self.posicion + 1 < len(self.tokens) and self.tokens[self.posicion] == '[' and self.tokens[self.posicion+1] == '[':
                self.consumir('[')
                tiene_wrapper = True

            matriz = []
            while self.posicion < len(self.tokens) and self.tokens[self.posicion] == '[':
                fila = []
                self.consumir('[')
                while self.tokens[self.posicion] != ']':
                    val = self.consumir()
                    if val != ',':
                        fila.append(int(val))
                self.consumir(']')
                matriz.append(fila)
                
                # Ignorar comas entre arreglos de Tanks
                if tiene_wrapper and self.tokens[self.posicion] == ',':
                    self.consumir(',')
            
            if tiene_wrapper and self.tokens[self.posicion] == ']':
                self.consumir(']')

            propiedades["states"].append(matriz)
            
        if self.posicion < len(self.tokens) and self.tokens[self.posicion] == 'END':
            self.consumir('END')
            
        self.ast['shapes'][nombre_shape] = propiedades

    def parsear_level_body(self):
        num_nivel = int(self.consumir())
        score_goal = 50
        mapa = []

        if self.posicion < len(self.tokens) and self.tokens[self.posicion] == 'SCORE_GOAL':
            self.consumir('SCORE_GOAL')
            score_goal = int(self.consumir())

        if self.posicion < len(self.tokens) and self.tokens[self.posicion] == 'MAP':
            self.consumir('MAP')
            self.consumir(':')
            while self.posicion < len(self.tokens) and self.tokens[self.posicion] == '[':
                fila = []
                self.consumir('[')
                while self.tokens[self.posicion] != ']':
                    simbolo = self.consumir()
                    fila.append(simbolo)
                self.consumir(']')
                mapa.append(fila)

        self.consumir('END')
        self.ast['levels'][str(num_nivel)] = {
            "score_goal": score_goal,
            "map": mapa
        }

    def parsear_evento(self):
        self.consumir('ON')
        nombre_evento = self.consumir()

        # Soporte para reglas de puntuacion: ON TARGET_SCORE 1000
        if nombre_evento == 'TARGET_SCORE':
            puntos = self.consumir()
            nombre_evento = "TARGET_SCORE_" + puntos

        if self.posicion < len(self.tokens) and self.tokens[self.posicion] != ':':
            sufijo = self.tokens[self.posicion]
            # Evitamos colisionar con acciones en la misma linea de Tanks
            if sufijo not in ['END', 'SPAWN', 'MOVE', 'ROTATE', 'GROW', 'INCREASE_SCORE', 'CHANGE_DIRECTION', 'SET_DIRECTION', 'SHOOT', 'GAME_OVER', 'NEXT_LEVEL', 'RESET_SNAKE']:
                nombre_evento += "_" + self.consumir()

        if self.posicion < len(self.tokens) and self.tokens[self.posicion] == ':':
            self.consumir(':')
            
        acciones = []
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] != 'END':
            token_acc = self.consumir()
            accion_obj = {"type": token_acc}

            if token_acc == 'SPAWN':
                accion_obj['target'] = self.consumir()
                if self.posicion < len(self.tokens) and self.tokens[self.posicion] == 'AT':
                    self.consumir('AT')
                    if self.posicion < len(self.tokens) and self.tokens[self.posicion] == 'RANDOM':
                        self.consumir('RANDOM')
                    elif self.posicion < len(self.tokens) and self.tokens[self.posicion] == '(':
                        self.consumir('(')
                        x = int(self.consumir())
                        self.consumir(',')
                        y = int(self.consumir())
                        self.consumir(')')
                        accion_obj['params'] = [[x, y]]
            elif token_acc == 'MOVE':
                accion_obj['target'] = self.consumir()
                if self.posicion < len(self.tokens) and self.tokens[self.posicion] in ['LEFT', 'RIGHT', 'DOWN', 'UP', 'FORWARD']:
                    accion_obj['direction'] = self.consumir()
            elif token_acc == 'ROTATE':
                accion_obj['target'] = self.consumir()
            elif token_acc == 'GROW':
                accion_obj['target'] = self.consumir()
                if self.posicion < len(self.tokens) and self.tokens[self.posicion].isdigit():
                    self.consumir()
            elif token_acc == 'INCREASE_SCORE':
                accion_obj['value'] = int(self.consumir())
            elif token_acc in ['CHANGE_DIRECTION', 'SET_DIRECTION']:
                accion_obj['type'] = 'CHANGE_DIRECTION'
                accion_obj['direction'] = self.consumir()
            elif token_acc == 'SHOOT':
                accion_obj['target'] = self.consumir()

            acciones.append(accion_obj)

        self.consumir('END')
        self.ast['events'][nombre_evento] = acciones

def generar_codigo(ast, archivo_salida):
    with open(archivo_salida, 'w') as f:
        json.dump(ast, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python compiler.py <archivo_entrada.brick>")
        sys.exit(1)
    archivo_entrada = sys.argv[1]
    archivo_salida = archivo_entrada.replace('.brick', '.json')
    print("Compilando " + archivo_entrada + "...")
    try:
        with open(archivo_entrada, 'r') as f:
            codigo = f.read()
        tokens = lexer(codigo)
        parser = Parser(tokens)
        ast = parser.parse()
        generar_codigo(ast, archivo_salida)
        print("Compilacion exitosa! Archivo de juego creado en " + archivo_salida)
    except Exception as e:
        print("\n!!! ERROR DE COMPILACION !!!")
        print(str(e))
        sys.exit(1)