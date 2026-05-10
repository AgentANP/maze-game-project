import heapq
import math
import random
from collections import deque

WIDTH = 1200
HEIGHT = 760
SIDEBAR_W = 280
PADDING = 18
TOP_BAR_H = 72
BG = (18, 20, 26)
PANEL = (28, 32, 41)
PANEL_2 = (38, 43, 54)
TEXT = (238, 242, 248)
DIM = (170, 178, 192)
ACCENT_BFS = (0, 224, 206)
ACCENT_ASTAR = (247, 196, 96)
ACCENT_DFS = (190, 132, 242)
GREEN = (0, 224, 122)
RED = (245, 72, 98)
WALL = (5, 7, 11)
OPEN = (46, 54, 70)
VISITED = (48, 105, 100)
FRONTIER = (38, 86, 118)
BACKTRACK = (24, 54, 72)
PATH_BFS = ACCENT_BFS
PATH_ASTAR = ACCENT_ASTAR
PATH_DFS = ACCENT_DFS

GRID_LINE = (235, 238, 244, 45)
STATUS_BG = (22, 25, 32)
STATUS_BORDER = (66, 74, 89)

ALGO_CONFIG = {
    "bfs": {"name": "BFS", "path": PATH_BFS, "frontier": FRONTIER, "status": ACCENT_BFS},
    "astar": {"name": "A*", "path": PATH_ASTAR, "frontier": (42, 30, 0), "status": ACCENT_ASTAR},
    "dfs": {"name": "DFS", "path": PATH_DFS, "frontier": (26, 10, 46), "status": ACCENT_DFS},
}

START = (1, 1)


def get_end(n):
    return n - 2, n - 2


def shuffle(items):
    items = list(items)
    random.shuffle(items)
    return items


def in_bounds(r, c, n):
    return 0 <= r < n and 0 <= c < n


def reconstruct_path(parent, end):
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = parent[cur[0]][cur[1]]
    path.reverse()
    return path


def generate_maze(n, wall_density):
    grid = [[1 for _ in range(n)] for _ in range(n)]

    cells = []
    for r in range(1, n - 1, 2):
        for c in range(1, n - 1, 2):
            cells.append((r, c))

    if not cells:
        return grid

    in_maze = [[False for _ in range(n)] for _ in range(n)]

    sr, sc = cells[0]
    grid[sr][sc] = 0
    in_maze[sr][sc] = True
    in_maze_count = 1

    while in_maze_count < len(cells):
        unvisited = [cell for cell in cells if not in_maze[cell[0]][cell[1]]]
        if not unvisited:
            break

        cr, cc = random.choice(unvisited)
        path = [(cr, cc)]
        path_index = {(cr, cc): 0}
        r, c = cr, cc
        cell_dirs = [(-2, 0), (2, 0), (0, -2), (0, 2)]

        while not in_maze[r][c]:
            moved = False
            for dr, dc in shuffle(cell_dirs):
                nr, nc = r + dr, c + dc
                if 1 <= nr <= n - 2 and 1 <= nc <= n - 2:
                    if (nr, nc) in path_index:
                        idx = path_index[(nr, nc)]
                        for tail in path[idx + 1 :]:
                            path_index.pop(tail, None)
                        path = path[: idx + 1]
                    else:
                        path.append((nr, nc))
                        path_index[(nr, nc)] = len(path) - 1
                    r, c = nr, nc
                    moved = True
                    break
            if not moved:
                break

        for i, (pr, pc) in enumerate(path):
            grid[pr][pc] = 0
            if not in_maze[pr][pc]:
                in_maze[pr][pc] = True
                in_maze_count += 1
            if i > 0:
                lr, lc = path[i - 1]
                grid[(pr + lr) // 2][(pc + lc) // 2] = 0

    inner_size = (n - 2) * (n - 2)
    open_fraction = 1 - wall_density / 100.0
    extras = int(inner_size * open_fraction * 0.30)
    for _ in range(extras):
        r = random.randint(1, n - 2)
        c = random.randint(1, n - 2)
        if r % 2 == 0 or c % 2 == 0:
            grid[r][c] = 0

    end = get_end(n)
    grid[START[0]][START[1]] = 0
    grid[end[0]][end[1]] = 0

    er, ec = end
    has_open_neighbor = False
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = er + dr, ec + dc
        if 1 <= nr <= n - 2 and 1 <= nc <= n - 2 and grid[nr][nc] == 0:
            has_open_neighbor = True
            break
    if not has_open_neighbor and er - 1 >= 1:
        grid[er - 1][ec] = 0

    for i in range(n):
        grid[0][i] = 1
        grid[n - 1][i] = 1
        grid[i][0] = 1
        grid[i][n - 1] = 1

    return grid


def bfs(grid, start, end):
    n = len(grid)
    visited = [[False for _ in range(n)] for _ in range(n)]
    parent = [[None for _ in range(n)] for _ in range(n)]
    queue = deque([start])
    visited[start[0]][start[1]] = True
    steps = []

    while queue:
        r, c = queue.popleft()
        steps.append({"type": "visit", "r": r, "c": c})

        if (r, c) == end:
            steps.append({"type": "path", "cells": reconstruct_path(parent, end)})
            return steps

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc, n) and not visited[nr][nc] and grid[nr][nc] == 0:
                visited[nr][nc] = True
                parent[nr][nc] = (r, c)
                queue.append((nr, nc))
                steps.append({"type": "frontier", "r": nr, "c": nc})

    steps.append({"type": "no-path"})
    return steps


def astar(grid, start, end):
    n = len(grid)
    er, ec = end

    def heuristic(r, c):
        return abs(r - er) + abs(c - ec)

    infinity = math.inf
    g_score = [[infinity for _ in range(n)] for _ in range(n)]
    parent = [[None for _ in range(n)] for _ in range(n)]
    closed = [[False for _ in range(n)] for _ in range(n)]
    open_heap = [(heuristic(*start), start[0], start[1])]
    g_score[start[0]][start[1]] = 0
    steps = []

    while open_heap:
        _, r, c = heapq.heappop(open_heap)
        if closed[r][c]:
            continue

        closed[r][c] = True
        steps.append({"type": "visit", "r": r, "c": c})

        if (r, c) == end:
            steps.append({"type": "path", "cells": reconstruct_path(parent, end)})
            return steps

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc, n) or closed[nr][nc] or grid[nr][nc] != 0:
                continue

            tentative_g = g_score[r][c] + 1
            if tentative_g < g_score[nr][nc]:
                g_score[nr][nc] = tentative_g
                parent[nr][nc] = (r, c)
                heapq.heappush(open_heap, (tentative_g + heuristic(nr, nc), nr, nc))
                steps.append({"type": "frontier", "r": nr, "c": nc})

    steps.append({"type": "no-path"})
    return steps


def dfs(grid, start, end):
    n = len(grid)
    visited = [[False for _ in range(n)] for _ in range(n)]
    parent = [[None for _ in range(n)] for _ in range(n)]
    stack = [start]
    visited[start[0]][start[1]] = True
    steps = []

    while stack:
        r, c = stack[-1]
        steps.append({"type": "visit", "r": r, "c": c})

        if (r, c) == end:
            steps.append({"type": "path", "cells": reconstruct_path(parent, end)})
            return steps

        pushed = False
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc, n) and not visited[nr][nc] and grid[nr][nc] == 0:
                visited[nr][nc] = True
                parent[nr][nc] = (r, c)
                stack.append((nr, nc))
                steps.append({"type": "frontier", "r": nr, "c": nc})
                pushed = True
                break

        if not pushed:
            stack.pop()
            steps.append({"type": "backtrack", "r": r, "c": c})

    steps.append({"type": "no-path"})
    return steps
