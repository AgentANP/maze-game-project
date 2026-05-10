import pygame

from maze_core import (
    ACCENT_ASTAR,
    ACCENT_BFS,
    ACCENT_DFS,
    BACKTRACK,
    BG,
    DIM,
    GRID_LINE,
    GREEN,
    HEIGHT,
    OPEN,
    PANEL,
    RED,
    SIDEBAR_W,
    START,
    STATUS_BG,
    STATUS_BORDER,
    TEXT,
    VISITED,
    WALL,
    WIDTH,
    ALGO_CONFIG,
    generate_maze,
    get_end,
    bfs,
    astar,
    dfs,
)
from maze_widgets import Button, Slider


class MazeApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Maze Pathfinder - Python")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 18, bold=True)
        self.small_font = pygame.font.SysFont("arial", 15)
        self.title_font = pygame.font.SysFont("arial", 28, bold=True)
        self.active_font = pygame.font.SysFont("arial", 16, bold=True)

        self.size_slider = Slider((24, 110, 232, 22), 10, 30, 15, "Grid Size", ACCENT_BFS)
        self.density_slider = Slider((24, 186, 232, 22), 20, 55, 35, "Wall %", ACCENT_BFS)

        self.algo_buttons = {
            "bfs": Button((24, 250, 232, 42), "BFS", ACCENT_BFS),
            "astar": Button((24, 302, 232, 42), "A*", ACCENT_ASTAR),
            "dfs": Button((24, 354, 232, 42), "DFS", ACCENT_DFS),
        }

        self.speed_buttons = {
            120: Button((24, 430, 68, 38), "SLOW", ACCENT_BFS),
            40: Button((98, 430, 68, 38), "MED", ACCENT_BFS),
            8: Button((172, 430, 68, 38), "FAST", ACCENT_BFS),
        }

        self.btn_generate = Button((24, 490, 108, 44), "NEW MAZE", ACCENT_BFS, fill=(14, 26, 30))
        self.btn_run = Button((148, 490, 108, 44), "RUN BFS", ACCENT_BFS, fill=ACCENT_BFS, text_color=(5, 10, 12))

        self.selected_algo = "bfs"
        self.speed_ms = 40
        self.running = False
        self.steps = []
        self.step_index = 0
        self.path_draw_index = 0
        self.path_cells = []
        self.path_timer = 0
        self.anim_timer = 0
        self.visited_count = 0
        self.grid = []
        self.cell_state = []
        self.cell_size = 24
        self.grid_offset = (0, 0)
        self.status = "Generate a maze to begin."
        self.status_color = DIM
        self.stat_visited = "-"
        self.stat_path = "-"
        self.stat_grid = "-"
        self.maze_rect = pygame.Rect(0, 0, 0, 0)
        self.update_algo_style()
        self.generate_new()

    def algo_config(self, key=None):
        return ALGO_CONFIG[key or self.selected_algo]

    def get_algorithm_name(self, key=None):
        return self.algo_config(key)["name"]

    def update_algo_style(self):
        config = self.algo_config()
        for key, btn in self.algo_buttons.items():
            btn.active = key == self.selected_algo
        for btn in self.speed_buttons.values():
            btn.active = False
        self.speed_buttons[self.speed_ms].active = True
        self.btn_run.text = f"RUN {config['name']}"
        self.btn_run.accent = config["path"] if self.grid else ACCENT_BFS
        self.btn_run.fill = self.btn_run.accent
        self.btn_run.text_color = (5, 10, 12) if self.selected_algo == "bfs" else (10, 5, 10)
        self.btn_generate.accent = config["path"] if self.grid else ACCENT_BFS

    def compute_cell_size(self, n):
        maze_area_w = WIDTH - SIDEBAR_W - 3 * 18
        maze_area_h = HEIGHT - 72 - 2 * 18
        return max(12, min(34, min(maze_area_w // n, maze_area_h // n)))

    def resize_maze_geometry(self):
        n = len(self.grid) if self.grid else self.size_slider.value
        self.cell_size = self.compute_cell_size(n)
        maze_w = n * self.cell_size
        maze_h = n * self.cell_size
        panel_x = SIDEBAR_W + 18
        panel_y = 72
        self.grid_offset = (
            panel_x + max(0, (WIDTH - panel_x - 18 - maze_w) // 2),
            panel_y + max(0, (HEIGHT - panel_y - 18 - maze_h) // 2),
        )
        self.maze_rect = pygame.Rect(self.grid_offset[0], self.grid_offset[1], maze_w, maze_h)

    def reset_search_state(self, keep_status=False):
        self.cell_state = [["open" if cell == 0 else "wall" for cell in row] for row in self.grid]
        self.steps = []
        self.step_index = 0
        self.path_draw_index = 0
        self.path_cells = []
        self.path_timer = 0
        self.anim_timer = 0
        self.visited_count = 0
        self.stat_visited = "-"
        self.stat_path = "-"
        if not keep_status:
            self.status = f"Maze ready. Press RUN {self.get_algorithm_name()}."
            self.status_color = DIM

    def reset_search_ui(self):
        self.reset_search_state()
        self.running = False
        self.btn_generate.enabled = True
        self.btn_run.enabled = True

    def generate_new(self):
        if self.running:
            return
        n = int(self.size_slider.value)
        density = int(self.density_slider.value)
        self.grid = generate_maze(n, density)
        self.reset_search_state(keep_status=True)
        self.resize_maze_geometry()
        self.stat_grid = f"{n}x{n}"
        self.btn_run.enabled = True
        self.btn_generate.enabled = True
        self.update_algo_style()

    def start_run(self):
        if self.running:
            return
        self.reset_search_state()
        self.resize_maze_geometry()
        self.steps = self.run_selected_algorithm()
        self.stat_visited = "0"
        self.status = "Searching..."
        self.status_color = self.algo_config()["status"]
        self.running = True
        self.btn_generate.enabled = False
        self.btn_run.enabled = False

    def run_selected_algorithm(self):
        start = START
        end = get_end(len(self.grid))
        if self.selected_algo == "bfs":
            return bfs(self.grid, start, end)
        if self.selected_algo == "astar":
            return astar(self.grid, start, end)
        return dfs(self.grid, start, end)

    def is_start_or_end(self, r, c):
        end = get_end(len(self.grid))
        return (r, c) == START or (r, c) == end

    def set_cell_state(self, r, c, state):
        if self.cell_state and not self.is_start_or_end(r, c):
            self.cell_state[r][c] = state

    def draw_cell(self, r, c, color):
        x = self.grid_offset[0] + c * self.cell_size
        y = self.grid_offset[1] + r * self.cell_size
        rect = pygame.Rect(x + 1, y + 1, self.cell_size - 2, self.cell_size - 2)
        pygame.draw.rect(self.screen, color, rect)

    def draw_grid(self):
        self.screen.fill(BG)
        pygame.draw.rect(self.screen, PANEL, (0, 0, SIDEBAR_W, HEIGHT))
        pygame.draw.rect(self.screen, (16, 18, 23), (SIDEBAR_W, 0, WIDTH - SIDEBAR_W, HEIGHT))

        self.resize_maze_geometry()
        config = self.algo_config()

        for r, row in enumerate(self.grid):
            for c, val in enumerate(row):
                state = self.cell_state[r][c] if self.cell_state else ("wall" if val == 1 else "open")
                if state == "wall":
                    color = WALL
                elif state == "visited":
                    color = VISITED
                elif state == "frontier":
                    color = config["frontier"]
                elif state == "backtrack":
                    color = BACKTRACK
                elif state == "path":
                    color = config["path"]
                else:
                    color = OPEN
                self.draw_cell(r, c, color)

        for i in range(len(self.grid) + 1):
            x = self.grid_offset[0] + i * self.cell_size
            y = self.grid_offset[1] + i * self.cell_size
            pygame.draw.line(self.screen, GRID_LINE, (x, self.grid_offset[1]), (x, self.grid_offset[1] + len(self.grid) * self.cell_size), 1)
            pygame.draw.line(self.screen, GRID_LINE, (self.grid_offset[0], y), (self.grid_offset[0] + len(self.grid) * self.cell_size, y), 1)

        self.draw_start_end()
        title = self.title_font.render("MAZE PATHFINDER", True, ACCENT_BFS)
        self.screen.blit(title, (24, 20))
        self.draw_sidebar()
        self.draw_progress_bar()

    def draw_start_end(self):
        end = get_end(len(self.grid))
        for cell, color, label in ((START, GREEN, "S"), (end, RED, "E")):
            r, c = cell
            self.draw_cell(r, c, color)
            font = pygame.font.SysFont("arial", max(12, int(self.cell_size * 0.45)), bold=True)
            text = font.render(label, True, (8, 10, 12))
            x = self.grid_offset[0] + c * self.cell_size + self.cell_size // 2
            y = self.grid_offset[1] + r * self.cell_size + self.cell_size // 2
            self.screen.blit(text, text.get_rect(center=(x, y)))

    def draw_progress_bar(self):
        bar_x = SIDEBAR_W + 24
        bar_y = HEIGHT - 26
        bar_w = WIDTH - SIDEBAR_W - 48
        pygame.draw.rect(self.screen, (40, 45, 58), (bar_x, bar_y, bar_w, 5), border_radius=3)
        if self.grid:
            total_open = sum(1 for row in self.grid for cell in row if cell == 0)
            progress = 0 if total_open == 0 else min(1.0, self.visited_count / total_open)
            color = self.algo_config()["path"]
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, int(bar_w * progress), 5), border_radius=3)

    def draw_sidebar(self):
        left = 24
        self.size_slider.draw(self.screen, self.font, self.small_font)
        self.density_slider.draw(self.screen, self.font, self.small_font)

        algo_heading = self.small_font.render("Algorithm", True, DIM)
        self.screen.blit(algo_heading, (left, 230))
        for btn in self.algo_buttons.values():
            btn.draw(self.screen, self.active_font)

        speed_heading = self.small_font.render("Speed", True, DIM)
        self.screen.blit(speed_heading, (left, 406))
        for btn in self.speed_buttons.values():
            btn.draw(self.screen, self.active_font)

        self.btn_generate.draw(self.screen, self.active_font)
        self.btn_run.draw(self.screen, self.active_font)

        stats_heading = self.small_font.render("Stats", True, DIM)
        self.screen.blit(stats_heading, (left, 556))
        self.draw_stat_row(584, "Algorithm", self.get_algorithm_name(), self.algo_config()["path"])
        self.draw_stat_row(612, "Visited", self.stat_visited, TEXT)
        self.draw_stat_row(640, "Path Len", self.stat_path, TEXT)
        self.draw_stat_row(668, "Grid", self.stat_grid, TEXT)

        status_box = pygame.Rect(18, 694, 244, 42)
        pygame.draw.rect(self.screen, STATUS_BG, status_box, border_radius=8)
        pygame.draw.rect(self.screen, STATUS_BORDER, status_box, width=1, border_radius=8)
        status = self.small_font.render(self.status, True, self.status_color)
        self.screen.blit(status, (26, 707))

    def draw_stat_row(self, y, key, value, value_color):
        key_surface = self.small_font.render(key, True, DIM)
        value_surface = self.small_font.render(value, True, value_color)
        self.screen.blit(key_surface, (24, y))
        self.screen.blit(value_surface, (230 - value_surface.get_width(), y))

    def handle_event(self, event):
        if self.size_slider.handle_event(event):
            self.update_algo_style()
            return
        if self.density_slider.handle_event(event):
            self.update_algo_style()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_generate.contains(event.pos):
                self.generate_new()
                return
            if self.btn_run.contains(event.pos) and self.btn_run.enabled:
                self.start_run()
                return

            for key, btn in self.algo_buttons.items():
                if btn.contains(event.pos) and not self.running:
                    self.selected_algo = key
                    self.reset_search_ui()
                    self.update_algo_style()
                    return

            for speed, btn in self.speed_buttons.items():
                if btn.contains(event.pos):
                    self.speed_ms = speed
                    self.update_algo_style()
                    return

    def run_animation_step(self, dt_ms):
        if not self.running:
            return

        self.anim_timer += dt_ms
        step_delay = max(1, self.speed_ms)
        batch_size = 8 if self.speed_ms < 15 else 1

        while self.anim_timer >= step_delay and self.step_index < len(self.steps):
            self.anim_timer -= step_delay
            for _ in range(batch_size):
                if self.step_index >= len(self.steps):
                    break

                step = self.steps[self.step_index]
                self.step_index += 1

                if step["type"] == "visit":
                    r, c = step["r"], step["c"]
                    self.set_cell_state(r, c, "visited")
                    self.visited_count += 1
                elif step["type"] == "frontier":
                    r, c = step["r"], step["c"]
                    self.set_cell_state(r, c, "frontier")
                elif step["type"] == "backtrack":
                    r, c = step["r"], step["c"]
                    self.set_cell_state(r, c, "backtrack")
                elif step["type"] == "path":
                    self.path_cells = step["cells"]
                    self.path_draw_index = 0
                    self.status = "Path found."
                    self.status_color = self.algo_config()["path"]
                    self.stat_path = str(len(self.path_cells))
                    self.stat_visited = str(self.visited_count)
                    self.step_index = len(self.steps)
                    self.draw_path_step()
                    return
                elif step["type"] == "no-path":
                    self.status = "No path found."
                    self.status_color = RED
                    self.stat_path = "-"
                    self.stat_visited = str(self.visited_count)
                    self.running = False
                    self.btn_generate.enabled = True
                    self.btn_run.enabled = True
                    self.update_algo_style()
                    return

            self.stat_visited = str(self.visited_count)

        if self.step_index >= len(self.steps) and not self.path_cells:
            self.running = False
            self.btn_generate.enabled = True
            self.btn_run.enabled = True
            self.update_algo_style()

    def draw_path_step(self):
        if not self.path_cells:
            self.running = False
            self.btn_generate.enabled = True
            self.btn_run.enabled = True
            self.update_algo_style()
            return

        if self.path_draw_index >= len(self.path_cells):
            self.draw_start_end()
            self.stat_path = str(len(self.path_cells))
            self.stat_visited = str(self.visited_count)
            self.status = f"Path found. Length: {len(self.path_cells)}"
            self.status_color = self.algo_config()["path"]
            self.running = False
            self.btn_generate.enabled = True
            self.btn_run.enabled = True
            self.update_algo_style()
            return

        r, c = self.path_cells[self.path_draw_index]
        self.set_cell_state(r, c, "path")
        self.path_draw_index += 1

    def update(self, dt_ms):
        if self.running and self.path_cells:
            self.path_timer += dt_ms
            path_delay = max(18, int(self.speed_ms * 0.55))
            while self.path_timer >= path_delay and self.running:
                self.path_timer -= path_delay
                self.draw_path_step()
        elif self.running:
            self.run_animation_step(dt_ms)

    def draw(self):
        self.draw_grid()
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt_ms = self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    self.handle_event(event)

            self.update(dt_ms)
            self.draw()

        pygame.quit()


def main():
    app = MazeApp()
    app.run()


if __name__ == "__main__":
    main()
