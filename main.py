import tkinter as tk
from tkinter import messagebox
import pygame
import threading
import random
import math
import time
import mysql.connector

# Conexión a la base de datos
db_connection = mysql.connector.connect(
    host="junction.proxy.rlwy.net",
    user="root",
    password="GOFabdSxQGCDBwukZDJJpgIRqohPYfvf",
    database="DB_PARCIAL",
    port=29212,
    auth_plugin='mysql_native_password'
)
cursor = db_connection.cursor()

# Inicializamos Pygame
pygame.init()
pygame.mixer.init()

# Crear una ventana para solicitar los datos del usuario y registrarlo en la base de datos
def user_registration():
    # Crear la ventana
    window = tk.Tk()
    window.geometry("300x200")
    window.title("Registro de Usuario")

    # Etiquetas y campos de entrada
    tk.Label(window, text="Nombre:").pack(pady=5)
    name_entry = tk.Entry(window)
    name_entry.pack(pady=5)

    # Función para validar y procesar los datos
    def start_game():
        name = name_entry.get()

        if not name:
            messagebox.showerror("Error", "Por favor, ingresa un nombre válido.")
        else:
            # Registrar el jugador en la base de datos
            try:
                cursor.execute("INSERT INTO Jugadores (nombre) VALUES (%s)", (name,))
                db_connection.commit()
                print(f"Jugador {name} registrado en la base de datos.")
            except mysql.connector.Error as err:
                print(f"Error al registrar el jugador: {err}")
            finally:
                cursor.reset()

            # Cerrar la ventana de registro
            window.destroy()
            main_game(name)  # Iniciar el juego pasando el nombre del usuario

    # Botón de inicio
    start_button = tk.Button(window, text="Iniciar Juego", command=start_game)
    start_button.pack(pady=10)

    # Ejecutar el bucle de la ventana de registro
    window.mainloop()

# Lógica del juego 2048
def main_game(player_name):
    pygame.mixer.music.load("musica.mp3")
    pygame.mixer.music.play(-1)

    FPS = 60
    WIDTH, HEIGHT = 800, 800
    ROWS = 4
    COLS = 4

    RECT_HEIGHT = HEIGHT // ROWS
    RECT_WIDTH = WIDTH // COLS

    OUTLINE_COLOR = (187, 173, 160)
    OUTLINE_THICKNESS = 10
    BACKGROUND_COLOR = (205, 192, 180)
    FONT_COLOR = (119, 110, 101)

    FONT = pygame.font.SysFont("comicsans", 60, bold=True)
    MOVE_VEL = 50

    WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"2048 - Jugador: {player_name}")

    # Ventana emergente usando tkinter
    class ScoreWindow(tk.Tk):
        def __init__(self, move_callback):
            super().__init__()
            self.title("Puntaje, Tiempo y Controles")
            self.geometry("300x250")

            self.score_label = tk.Label(self, text="Puntaje: 0", font=("Helvetica", 10))
            self.score_label.pack(pady=10)

            self.time_label = tk.Label(self, text="Tiempo: 0s", font=("Helvetica", 10))
            self.time_label.pack(pady=10)

            # Botones de votación
            def votar(direccion):
                try:
                    cursor.execute(
                        "INSERT INTO Votos (id_jugador, direccion) VALUES (%s, %s)",
                        (1, direccion)  # ID del jugador como ejemplo
                    )
                    db_connection.commit()
                    print(f"Voto registrado: {direccion}")
                except mysql.connector.Error as err:
                    print(f"Error al guardar el voto: {err}")
                finally:
                    cursor.reset()

            self.up_button = tk.Button(self, text="Arriba", width=10, command=lambda: votar("Arriba"))
            self.up_button.pack(pady=5)

            self.left_right_frame = tk.Frame(self)
            self.left_right_frame.pack(pady=10)

            self.left_button = tk.Button(self.left_right_frame, text="Izquierda", width=10, command=lambda: votar("Izquierda"))
            self.left_button.pack(side="left", padx=20)

            self.right_button = tk.Button(self.left_right_frame, text="Derecha", width=10, command=lambda: votar("Derecha"))
            self.right_button.pack(side="right", padx=20)

            self.down_button = tk.Button(self, text="Abajo", width=10, command=lambda: votar("Abajo"))
            self.down_button.pack(pady=10)

            self.protocol("WM_DELETE_WINDOW", self.on_closing)

        def update_score(self, score):
            self.score_label.config(text=f"Puntaje: {score}")

        def update_time(self, elapsed_time):
            self.time_label.config(text=f"Tiempo: {elapsed_time}s")

        def on_closing(self):
            pass

    # Clase para manejar las casillas del juego
    class Tile:
        COLORS = [
            (237, 229, 218),
            (238, 225, 201),
            (243, 178, 122),
            (246, 150, 101),
            (247, 124, 95),
            (247, 95, 59),
            (237, 208, 115),
            (237, 204, 99),
            (236, 202, 80),
        ]

        def __init__(self, value, row, col):
            self.value = value
            self.row = row
            self.col = col
            self.x = col * RECT_WIDTH
            self.y = row * RECT_HEIGHT

        def get_color(self):
            color_index = int(math.log2(self.value)) - 1
            color = self.COLORS[color_index]
            return color

        def draw(self, window):
            color = self.get_color()
            pygame.draw.rect(window, color, (self.x, self.y, RECT_WIDTH, RECT_HEIGHT))

            text = FONT.render(str(self.value), 1, FONT_COLOR)
            window.blit(
                text,
                (
                    self.x + (RECT_WIDTH / 2 - text.get_width() / 2),
                    self.y + (RECT_HEIGHT / 2 - text.get_height() / 2),
                ),
            )

        def set_pos(self, ceil=False):
            if ceil:
                self.row = math.ceil(self.y / RECT_HEIGHT)
                self.col = math.ceil(self.x / RECT_WIDTH)
            else:
                self.row = math.floor(self.y / RECT_HEIGHT)
                self.col = math.floor(self.x / RECT_WIDTH)

        def move(self, delta):
            self.x += delta[0]
            self.y += delta[1]

    def draw_grid(window):
        for row in range(1, ROWS):
            y = row * RECT_HEIGHT
            pygame.draw.line(window, OUTLINE_COLOR, (0, y), (WIDTH, y), OUTLINE_THICKNESS)

        for col in range(1, COLS):
            x = col * RECT_WIDTH
            pygame.draw.line(window, OUTLINE_COLOR, (x, 0), (x, HEIGHT), OUTLINE_THICKNESS)

        pygame.draw.rect(window, OUTLINE_COLOR, (0, 0, WIDTH, HEIGHT), OUTLINE_THICKNESS)

    def draw(window, tiles):
        window.fill(BACKGROUND_COLOR)
        for tile in tiles.values():
            tile.draw(window)
        draw_grid(window)
        pygame.display.update()

    def get_random_pos(tiles):
        while True:
            row = random.randrange(0, ROWS)
            col = random.randrange(0, COLS)
            if f"{row}{col}" not in tiles:
                return row, col

    # Movimiento de las casillas
    def move_tiles(window, tiles, clock, direction, score):
        updated = True
        blocks = set()

        if direction == "Izquierda":
            sort_func = lambda x: x.col
            reverse = False
            delta = (-MOVE_VEL, 0)
            boundary_check = lambda tile: tile.col == 0
            get_next_tile = lambda tile: tiles.get(f"{tile.row}{tile.col - 1}")
            merge_check = lambda tile, next_tile: tile.x > next_tile.x + MOVE_VEL
            move_check = lambda tile, next_tile: tile.x > next_tile.x + RECT_WIDTH + MOVE_VEL
            ceil = True
        elif direction == "Derecha":
            sort_func = lambda x: x.col
            reverse = True
            delta = (MOVE_VEL, 0)
            boundary_check = lambda tile: tile.col == COLS - 1
            get_next_tile = lambda tile: tiles.get(f"{tile.row}{tile.col + 1}")
            merge_check = lambda tile, next_tile: tile.x < next_tile.x - MOVE_VEL
            move_check = lambda tile, next_tile: tile.x + RECT_WIDTH + MOVE_VEL < next_tile.x
            ceil = False
        elif direction == "Arriba":
            sort_func = lambda x: x.row
            reverse = False
            delta = (0, -MOVE_VEL)
            boundary_check = lambda tile: tile.row == 0
            get_next_tile = lambda tile: tiles.get(f"{tile.row - 1}{tile.col}")
            merge_check = lambda tile, next_tile: tile.y > next_tile.y + MOVE_VEL
            move_check = lambda tile, next_tile: tile.y > next_tile.y + RECT_HEIGHT + MOVE_VEL
            ceil = True
        elif direction == "Abajo":
            sort_func = lambda x: x.row
            reverse = True
            delta = (0, MOVE_VEL)
            boundary_check = lambda tile: tile.row == ROWS - 1
            get_next_tile = lambda tile: tiles.get(f"{tile.row + 1}{tile.col}")
            merge_check = lambda tile, next_tile: tile.y < next_tile.y - MOVE_VEL
            move_check = lambda tile, next_tile: tile.y + RECT_HEIGHT + MOVE_VEL < next_tile.y
            ceil = False

        while updated:
            clock.tick(FPS)
            updated = False
            sorted_tiles = sorted(tiles.values(), key=sort_func, reverse=reverse)

            for i, tile in enumerate(sorted_tiles):
                if boundary_check(tile):
                    continue

                next_tile = get_next_tile(tile)
                if not next_tile:
                    tile.move(delta)
                elif tile.value == next_tile.value and tile not in blocks and next_tile not in blocks:
                    if merge_check(tile, next_tile):
                        tile.move(delta)
                    else:
                        next_tile.value *= 2
                        score += next_tile.value  # Add to score
                        sorted_tiles.pop(i)
                        blocks.add(next_tile)
                elif move_check(tile, next_tile):
                    tile.move(delta)
                else:
                    continue

                tile.set_pos(ceil)
                updated = True

            update_tiles(window, tiles, sorted_tiles)

        return end_move(tiles), score

    def end_move(tiles):
        if len(tiles) == 16:
            return "lost"

        row, col = get_random_pos(tiles)
        tiles[f"{row}{col}"] = Tile(random.choice([2, 4]), row, col)
        return "continue"

    def update_tiles(window, tiles, sorted_tiles):
        tiles.clear()
        for tile in sorted_tiles:
            tiles[f"{tile.row}{tile.col}"] = tile
        draw(window, tiles)

    def generate_tiles():
        tiles = {}
        for _ in range(2):
            row, col = get_random_pos(tiles)
            tiles[f"{row}{col}"] = Tile(2, row, col)
        return tiles

    # Función para ejecutar el procedimiento almacenado para contabilizar votos
    def obtener_movimiento_ganador():
        global movimiento_ganador
        try:
            # Ejecutar el procedimiento almacenado con multi=True
            for result in cursor.execute("CALL ContabilizarVotos()", multi=True):
                if result.with_rows:
                    movimiento_ganador = result.fetchone()[0]
                    print(f"Movimiento ganador: {movimiento_ganador}")
        except mysql.connector.Error as err:
            print(f"Error al obtener el movimiento ganador: {err}")
        finally:
            cursor.reset()

    # Función principal del juego
    def main(window):
        clock = pygame.time.Clock()
        tiles = generate_tiles()
        score = 0
        start_time = pygame.time.get_ticks()

        def handle_move(direction):
            nonlocal score
            result, score = move_tiles(window, tiles, clock, direction, score)
            if result == "lost":
                elapsed_time = (pygame.time.get_ticks() - start_time) // 1000
                print(f"Game over! Final Score: {score}, Time played: {elapsed_time}s")
                score_window.destroy()  # Cerrar la ventana de puntuación
                pygame.quit()

        score_window = ScoreWindow(move_callback=handle_move)
        score_window.update()

        # Temporizador de 1 minuto para contabilizar los votos
        def temporizador_votacion():
            global movimiento_ganador  # Asegurarnos de que estamos trabajando con la variable global
            while True:
                time.sleep(60)  # Pausa de 1 minuto para el temporizador
                obtener_movimiento_ganador()  # Obtener el movimiento ganador desde la base de datos
                if movimiento_ganador:
                    handle_move(movimiento_ganador)
                    movimiento_ganador = None  # Reiniciar el movimiento ganador después de aplicarlo

        threading.Thread(target=temporizador_votacion, daemon=True).start()

        while True:
            elapsed_time = (pygame.time.get_ticks() - start_time) // 1000
            score_window.update_score(score)
            score_window.update_time(elapsed_time)
            draw(window, tiles)
            score_window.update()

        pygame.quit()

    main(WINDOW)

# Ejecutar el proceso de registro y juego
user_registration()
