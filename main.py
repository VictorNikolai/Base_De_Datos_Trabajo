import pygame
import random
import math
import time
import tkinter as tk
from tkinter import messagebox
from threading import Thread
import mysql.connector

# Conexión a la base de datos usando las credenciales proporcionadas
db_connection = mysql.connector.connect(
    host="junction.proxy.rlwy.net",
    user="root",
    password="EtVQMDlMtovPjPwbPqnTUnnVAWcAglfV",
    database="DB_PARCIAL",
    port=51751,
    auth_plugin='mysql_native_password'
)
cursor = db_connection.cursor()

# Inicializar Pygame
pygame.init()
pygame.mixer.init()

# Cargar música
pygame.mixer.music.load("musica.mp3")
pygame.mixer.music.play(-1)

# Configuración del juego
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
SMALL_FONT = pygame.font.SysFont("comicsans", 40, bold=True)
MOVE_VEL = 20
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2048")

# Variable global para almacenar el voto desde la Ventana 1
voto = None
movimiento_ganador = None  # Movimiento determinado por los votos

# Clase de las casillas
class Tile:
    COLORS = [
        (237, 229, 218),  # Para valor 2
        (238, 225, 201),  # Para valor 4
        (243, 178, 122),  # Para valor 8
        (246, 150, 101),  # Para valor 16
        (247, 124, 95),   # Para valor 32
        (247, 95, 59),    # Para valor 64
        (237, 208, 115),  # Para valor 128
        (237, 204, 99),   # Para valor 256
        (236, 202, 80),   # Para valor 512
        (237, 207, 114),  # Para valor 1024
        (237, 203, 97)    # Para valor 2048
    ]

    def __init__(self, value, row, col):
        self.value = value
        self.row = row
        self.col = col
        self.x = col * RECT_WIDTH
        self.y = row * RECT_HEIGHT

    def get_color(self):
        # Verificar que el valor sea un número válido y dentro de los límites
        if self.value > 0 and int(math.log2(self.value)) - 1 < len(self.COLORS):
            color_index = int(math.log2(self.value)) - 1
            color = self.COLORS[color_index]
        else:
            color = (255, 255, 255)  # Color blanco por defecto si no se encuentra
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

# Dibuja la cuadrícula
def draw_grid(window):
    for row in range(1, ROWS):
        y = row * RECT_HEIGHT
        pygame.draw.line(window, OUTLINE_COLOR, (0, y), (WIDTH, y), OUTLINE_THICKNESS)
    for col in range(1, COLS):
        x = col * RECT_WIDTH
        pygame.draw.line(window, OUTLINE_COLOR, (x, 0), (x, HEIGHT), OUTLINE_THICKNESS)
    pygame.draw.rect(window, OUTLINE_COLOR, (0, 0, WIDTH, HEIGHT), OUTLINE_THICKNESS)

# Dibuja el tablero y la puntuación
def draw(window, tiles, score, start_time):
    window.fill(BACKGROUND_COLOR)
    for tile in tiles.values():
        tile.draw(window)
    draw_grid(window)
    score_text = SMALL_FONT.render(f"Score: {score}", 1, FONT_COLOR)
    window.blit(score_text, (10, 10))
    elapsed_time = (pygame.time.get_ticks() - start_time) // 1000
    time_text = SMALL_FONT.render(f"Time: {elapsed_time}s", 1, FONT_COLOR)
    window.blit(time_text, (WIDTH - 200, 10))
    pygame.display.update()

# Movimiento de las casillas
def move_tiles(tiles, direction):
    if direction == "Derecha":
        for row in range(ROWS):
            merged = [False] * COLS
            for col in range(COLS - 2, -1, -1):  # Iterar de derecha a izquierda
                if tiles.get(f"{row}{col}"):
                    current_tile = tiles[f"{row}{col}"]
                    for next_col in range(col + 1, COLS):  # Mover hacia la derecha
                        if not tiles.get(f"{row}{next_col}"):
                            # Mover la casilla
                            tiles[f"{row}{next_col}"] = current_tile
                            tiles[f"{row}{next_col}"].col = next_col
                            if f"{row}{col}" in tiles:  # Verificar que la casilla exista antes de eliminarla
                                del tiles[f"{row}{col}"]
                        elif tiles[f"{row}{next_col}"].value == current_tile.value and not merged[next_col]:
                            # Fusionar casillas
                            tiles[f"{row}{next_col}"].value *= 2
                            if f"{row}{col}" in tiles:  # Verificar que la casilla exista antes de eliminarla
                                del tiles[f"{row}{col}"]
                            merged[next_col] = True
                            break
                        else:
                            break  # No se puede mover más en esta dirección

    elif direction == "Izquierda":
        for row in range(ROWS):
            merged = [False] * COLS
            for col in range(1, COLS):  # Iterar de izquierda a derecha
                if tiles.get(f"{row}{col}"):
                    current_tile = tiles[f"{row}{col}"]
                    for next_col in range(col - 1, -1, -1):  # Mover hacia la izquierda
                        if not tiles.get(f"{row}{next_col}"):
                            # Mover la casilla
                            tiles[f"{row}{next_col}"] = current_tile
                            tiles[f"{row}{next_col}"].col = next_col
                            if f"{row}{col}" in tiles:  # Verificar que la casilla exista antes de eliminarla
                                del tiles[f"{row}{col}"]
                        elif tiles[f"{row}{next_col}"].value == current_tile.value and not merged[next_col]:
                            # Fusionar casillas
                            tiles[f"{row}{next_col}"].value *= 2
                            if f"{row}{col}" in tiles:  # Verificar que la casilla exista antes de eliminarla
                                del tiles[f"{row}{col}"]
                            merged[next_col] = True
                            break
                        else:
                            break  # No se puede mover más en esta dirección

    elif direction == "Arriba":
        for col in range(COLS):
            merged = [False] * ROWS
            for row in range(1, ROWS):  # Iterar de arriba hacia abajo
                if tiles.get(f"{row}{col}"):
                    current_tile = tiles[f"{row}{col}"]
                    for next_row in range(row - 1, -1, -1):  # Mover hacia arriba
                        if not tiles.get(f"{next_row}{col}"):
                            # Mover la casilla
                            tiles[f"{next_row}{col}"] = current_tile
                            tiles[f"{next_row}{col}"].row = next_row
                            if f"{row}{col}" in tiles:  # Verificar que la casilla exista antes de eliminarla
                                del tiles[f"{row}{col}"]
                        elif tiles[f"{next_row}{col}"].value == current_tile.value and not merged[next_row]:
                            # Fusionar casillas
                            tiles[f"{next_row}{col}"].value *= 2
                            if f"{row}{col}" in tiles:  # Verificar que la casilla exista antes de eliminarla
                                del tiles[f"{row}{col}"]
                            merged[next_row] = True
                            break
                        else:
                            break  # No se puede mover más en esta dirección

    elif direction == "Abajo":
        for col in range(COLS):
            merged = [False] * ROWS
            for row in range(ROWS - 2, -1, -1):  # Iterar de abajo hacia arriba
                if tiles.get(f"{row}{col}"):
                    current_tile = tiles[f"{row}{col}"]
                    for next_row in range(row + 1, ROWS):  # Mover hacia abajo
                        if not tiles.get(f"{next_row}{col}"):
                            # Mover la casilla
                            tiles[f"{next_row}{col}"] = current_tile
                            tiles[f"{next_row}{col}"].row = next_row
                            if f"{row}{col}" in tiles:  # Verificar que la casilla exista antes de eliminarla
                                del tiles[f"{row}{col}"]
                        elif tiles[f"{next_row}{col}"].value == current_tile.value and not merged[next_row]:
                            # Fusionar casillas
                            tiles[f"{next_row}{col}"].value *= 2
                            if f"{row}{col}" in tiles:  # Verificar que la casilla exista antes de eliminarla
                                del tiles[f"{row}{col}"]
                            merged[next_row] = True
                            break
                        else:
                            break  # No se puede mover más en esta dirección


# Ejecutar el procedimiento almacenado para contabilizar los votos
def obtener_movimiento_ganador():
    global movimiento_ganador
    try:
        # Ejecutar el procedimiento almacenado
        cursor.execute("CALL ContabilizarVotos()")

        # Verificar si el cursor tiene un resultado
        result = cursor.fetchone()
        if result:
            movimiento_ganador = result[0]  # Obtener el movimiento ganador actual
            if movimiento_ganador != 'Ninguno':
                print(f"Movimiento ganador: {movimiento_ganador}")
            else:
                print("No hubo suficiente votación para determinar un ganador.")
        else:
            print("No se encontró ningún movimiento ganador.")

        # Asegurarse de consumir todos los resultados antes de cerrar el cursor
        while cursor.nextset():
            pass
    except mysql.connector.Error as err:
        print(f"Error al obtener el movimiento ganador: {err}")
    finally:
        # Reiniciar el cursor después de usarlo
        cursor.reset()

# Función principal del juego (Ventana 2)
def main(window):
    clock = pygame.time.Clock()
    run = True
    tiles = generate_tiles()
    score = 0
    start_time = pygame.time.get_ticks()  # Tiempo de inicio

    while run:
        clock.tick(FPS)

        global voto, movimiento_ganador

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            # Capturar teclas del teclado
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    move_tiles(tiles, "Izquierda")
                elif event.key == pygame.K_RIGHT:
                    move_tiles(tiles, "Derecha")
                elif event.key == pygame.K_UP:
                    move_tiles(tiles, "Arriba")
                elif event.key == pygame.K_DOWN:
                    move_tiles(tiles, "Abajo")

        # Aplicar el movimiento ganador después de contabilizar los votos
        if movimiento_ganador and movimiento_ganador != 'Ninguno':
            print(f"Aplicando el movimiento: {movimiento_ganador}")
            move_tiles(tiles, movimiento_ganador)
            movimiento_ganador = None  # Reiniciar el movimiento después de aplicarlo

        draw(window, tiles, score, start_time)

    pygame.quit()

# Función para generar las casillas iniciales
def generate_tiles():
    tiles = {}
    for _ in range(2):
        row, col = get_random_pos(tiles)
        tiles[f"{row}{col}"] = Tile(2, row, col)
    return tiles

# Generar posiciones aleatorias en la cuadrícula
def get_random_pos(tiles):
    row = None
    col = None
    while True:
        row = random.randrange(0, ROWS)
        col = random.randrange(0, COLS)
        if f"{row}{col}" not in tiles:
            break
    return row, col

# Temporizador de 1 minuto y contabilización de votos
def temporizador_voto():
    while True:
        time.sleep(60)  # Pausa de 1 minuto para el temporizador
        obtener_movimiento_ganador()  # Obtener el movimiento ganador desde la base de datos
        # Asegurarse de que no haya comandos SQL pendientes antes de continuar
        cursor.reset()

# Ventana de votación (Tkinter)
def ventana_votacion():
    global voto

    def votar(direccion):
        global voto
        voto = direccion
        messagebox.showinfo("Votación", f"Votaste por {direccion}")
        # Insertar voto en la base de datos
        try:
            cursor.execute(
                "INSERT INTO Votos (id_jugador, direccion) VALUES (%s, %s)",
                (1, direccion)
            )
            db_connection.commit()
            print(f"Voto registrado: {direccion}")
        except mysql.connector.Error as err:
            print(f"Error al guardar el voto: {err}")
        finally:
            # Reiniciar el cursor para evitar errores de sincronización
            cursor.reset()

    root = tk.Tk()
    root.title("Ventana 1: Votación")
    frame = tk.Frame(root)
    frame.pack(padx=20, pady=20)
    btn_arriba = tk.Button(frame, text="Arriba", command=lambda: votar("Arriba"), width=10, height=2)
    btn_izquierda = tk.Button(frame, text="Izquierda", command=lambda: votar("Izquierda"), width=10, height=2)
    btn_abajo = tk.Button(frame, text="Abajo", command=lambda: votar("Abajo"), width=10, height=2)
    btn_derecha = tk.Button(frame, text="Derecha", command=lambda: votar("Derecha"), width=10, height=2)
    btn_arriba.grid(row=0, column=1, padx=10, pady=10)
    btn_izquierda.grid(row=1, column=0, padx=10, pady=10)
    btn_abajo.grid(row=2, column=1, padx=10, pady=10)
    btn_derecha.grid(row=1, column=2, padx=10, pady=10)
    root.mainloop()

# Función para ejecutar ambas ventanas en paralelo
def ejecutar_ventanas():
    # Ventana 1 en un hilo separado
    hilo_votacion = Thread(target=ventana_votacion)
    hilo_votacion.start()

    # Temporizador para la contabilización de votos
    hilo_temporizador = Thread(target=temporizador_voto)
    hilo_temporizador.start()

    # Ventana 2 con el juego
    main(WINDOW)

if __name__ == "__main__":
    ejecutar_ventanas()
