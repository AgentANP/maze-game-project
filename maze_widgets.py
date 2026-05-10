import pygame

from maze_core import PANEL_2, TEXT


class Button:
    def __init__(self, rect, text, accent, fill=None, text_color=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.accent = accent
        self.fill = fill or PANEL_2
        self.text_color = text_color or TEXT
        self.enabled = True
        self.active = False

    def draw(self, surface, font):
        fill = self.fill
        border = self.accent if self.active else (60, 70, 90)
        text_color = self.text_color
        if not self.enabled:
            fill = (34, 38, 47)
            border = (50, 55, 66)
            text_color = (100, 106, 118)

        pygame.draw.rect(surface, fill, self.rect, border_radius=8)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=8)
        label = font.render(self.text, True, text_color)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)

    def contains(self, pos):
        return self.rect.collidepoint(pos)


class Slider:
    def __init__(self, rect, minimum, maximum, value, label, accent):
        self.rect = pygame.Rect(rect)
        self.minimum = minimum
        self.maximum = maximum
        self.value = value
        self.label = label
        self.accent = accent
        self.dragging = False

    def set_from_pos(self, x):
        track_x = self.rect.x + 14
        track_w = self.rect.w - 28
        ratio = max(0.0, min(1.0, (x - track_x) / track_w))
        self.value = round(self.minimum + ratio * (self.maximum - self.minimum))

    def knob_pos(self):
        track_x = self.rect.x + 14
        track_w = self.rect.w - 28
        ratio = (self.value - self.minimum) / (self.maximum - self.minimum)
        return int(track_x + ratio * track_w)

    def draw(self, surface, font, small_font):
        label_text = f"{self.label}: {self.value}"
        label = small_font.render(label_text, True, TEXT)
        surface.blit(label, (self.rect.x, self.rect.y - 18))

        track_y = self.rect.y + self.rect.h // 2
        track_x = self.rect.x + 14
        track_w = self.rect.w - 28
        pygame.draw.line(surface, (60, 70, 85), (track_x, track_y), (track_x + track_w, track_y), 6)
        knob_x = self.knob_pos()
        pygame.draw.line(surface, self.accent, (track_x, track_y), (knob_x, track_y), 6)
        pygame.draw.circle(surface, self.accent, (knob_x, track_y), 10)
        pygame.draw.circle(surface, (255, 255, 255), (knob_x, track_y), 10, 1)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            track = self.rect.inflate(0, 14)
            if track.collidepoint(event.pos):
                self.dragging = True
                self.set_from_pos(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.set_from_pos(event.pos[0])
            return True
        return False
