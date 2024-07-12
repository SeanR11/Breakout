import time
import pygame

class Tool:
    def __init__(self, window, parent, size):
        self.window = window
        self.parent = parent
        self.font = 'ArcadeClassic'
        self.color = None
        self.background_color = None
        self.size = size
        self.box = pygame.rect.Rect(0, 0, 0, 0)
        self.tool = None
        self.border = None

    def event_handler(self, event):
        pass

    def draw(self):
        self.window.blit(self.tool, self.box)
        if self.border:
            pygame.draw.rect(self.window, (255, 255, 255),
                             (self.border[0][0], self.border[0][1], self.border[0][2], self.border[0][3]),
                             width=self.border[1])

    def set_border(self, width):
        self.border = [pygame.rect.Rect(self.box), width]

    def set_center(self, center):
        w, h = self.window.get_size()
        if 'v' in center:
            self.box.y = 0
            self.box.y = self.box.y + (h - self.box.h) // 2
        if 'h' in center:
            self.box.x = 0
            self.box.x = self.box.x + (w - self.box.w) // 2

    def mouse_is_hover(self, mouse_position):
        if self.box.x < mouse_position[0] < self.box.x + self.box.w and self.box.y < mouse_position[
            1] < self.box.y + self.box.h:
            return True
        else:
            return False

    def get_local_pos(self, mouse_position):
        box = self.parent.box
        x = mouse_position[0] - box.x
        y = mouse_position[1] - box.y
        return x, y

    def render_text(self, text, color):
        return pygame.font.SysFont(self.font, self.size).render(text, False, color, (0, 0, 0))



class Label(Tool):
    def __init__(self, window, parent, text, size, color, position, center=''):
        super().__init__(window, parent, size)
        self.color = color
        self.text = text
        self.tool = self.render_text(self.text, self.color)
        self.box = self.tool.get_rect()
        self.box.x, self.box.y = position
        if center:
            self.set_center(center)


class TextBox(Tool):
    def __init__(self, window, parent, placeholder, size, color, position, center='', limit=None):
        super().__init__(window, parent, size)
        self.color = color
        self.placeholder = placeholder
        self.text = ''
        self.key_down = False
        self.limit = limit
        self.tool = self.render_text(self.placeholder, self.color)
        self.box = self.tool.get_rect()
        self.box = self.tool.get_rect(topleft=position)
        if center:
            self.set_center(center)

    def event_handler(self, event):
        if event.type == pygame.KEYDOWN and not self.key_down:
            self.key_down = True
            key = pygame.key.name(event.key)
            if len(key) == 1 and len(self.text) <= self.limit:
                if self.text == '':
                    self.window.fill((0, 0, 0))
                self.text += key
            elif key == 'backspace' and len(self.text) >= 0:
                self.window.fill((0, 0, 0))
                self.text = self.text[:-1]
            elif key == 'space' and len(self.text) <= self.limit:
                self.text += ' '
            self.tool =  pygame.font.SysFont(self.font, self.size).render(self.text, False, self.color, (0, 0, 0))
            self.box.w, self.box.h = self.tool.get_size()
            self.set_center('h')
        if event.type == pygame.KEYUP:
            self.key_down = False

    def update_text(self, text):
        if len(text) == 1 and (self.limit is None or len(self.text) < self.limit):
            self.text += text
            self.tool =  self.render_text(self.text, self.color)
            self.box.size = self.tool.get_size()
            self.set_center('h')


class Button(Tool):
    def __init__(self, window, parent, text, size, color, hover_color, position, center='', action=print):
        super().__init__(window, parent, size)
        self.color = color
        self.hover_color = hover_color
        self.text = text
        self.action = action
        self.tool = self.render_text(self.text, self.color)
        self.box = self.tool.get_rect(topleft=position)
        if center:
            self.set_center(center)

    def event_handler(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if hasattr(self.parent, 'surface'):
            x, y = mouse_pos
            x -= self.parent.box.left
            y -= self.parent.box.top
            mouse_pos = (x, y)
        if self.mouse_is_hover(mouse_pos):
            self.tool = self.render_text(self.text, self.hover_color)
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.action()
        else:
            self.tool = self.render_text(self.text, self.color)


class Image(Tool):
    def __init__(self, window, parent, path, size, position, center='', action=None):
        super().__init__(window, parent, size)
        self.data = pygame.image.load(path)
        self.action = action
        self.scale(self.size)
        self.box.update(position[0], position[1], self.data.get_size()[0], self.data.get_size()[1])
        if center:
            self.set_center(center)

        self.tool = self.data

    def event_handler(self, event):
        if self.action:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.mouse_is_hover(self.get_local_pos(mouse_pos)):
                    self.action()

    def scale(self, new_size):
        self.data = pygame.transform.scale(self.data, new_size)


class Sprite(Tool):
    def __init__(self, window, parent, sprite_rect, size, position, center='', duplicate=-1):
        super().__init__(window, parent, size)
        self.sprite_sheet = pygame.image.load('assets/img/sprite_sheet.png').convert_alpha()
        self.data = self.get_sprite(*sprite_rect)
        self.scale(self.size)
        self.box.update(position[0], position[1], self.data.get_size()[0], self.data.get_size()[1])
        self.duplicate = duplicate
        if center:
            self.set_center(center)

        self.tool = self.data

    def draw(self):
        if self.duplicate != -1:
            for n in range(self.duplicate):
                self.window.blit(self.tool, (self.box.x + (self.box.w + 10) * n, self.box.y, self.box.w, self.box.h))
        else:
            super().draw()

    def get_sprite(self, x, y, width, height):
        sprite = pygame.Surface((width, height), pygame.SRCALPHA)
        sprite.blit(self.sprite_sheet, (0, 0), (x, y, width, height))
        return sprite

    def set_duplicate(self, amount):
        self.duplicate = amount

    def scale(self, new_size):
        self.data = pygame.transform.scale(self.data, new_size)
        self.box.size = new_size
        self.tool = self.data

    def rotate(self, angle):
        self.data = pygame.transform.rotate(self.data, 30)
        self.tool = self.data

    def update_position(self, new_position, center=''):
        self.box.topleft = new_position
        if center:
            self.set_center(center)

    def update_sprite(self, sprite_rect, size=None, rotation=None):
        self.data = self.get_sprite(*sprite_rect)
        if size is None:
            size = self.box.size
        self.scale(size)
        if rotation:
            self.data = pygame.transform.rotate(self.data, rotation)

        self.box.size = self.data.get_rect().size
        self.tool = self.data


class Surface(Tool):
    def __init__(self, window, parent, size, position, center='', border=None):
        super().__init__(window, parent, size)
        self.surface = pygame.surface.Surface(size)
        self.box.update(position[0], position[1], size[0], size[1])
        self.tool = self.surface
        self.objects = []
        if center:
            self.set_center(center)
        if border:
            self.set_border(border)

    def event_handler(self, event):
        for obj in self.objects:
            obj.event_handler(event)

    def draw(self):
        self.surface.fill((0, 0, 0))
        for obj in self.objects:
            obj.draw()

        super().draw()

    def add_object(self, obj):
        self.objects.append(obj)

    def remove_object(self, selected_object):
        for idx, obj in enumerate(self.objects):
            if obj == selected_object:
                del self.objects[idx]


class Shape(Tool):
    def __init__(self, window, parent, shape_type, name, size, position, color):
        super().__init__(window, parent, size)
        self.shape_type = shape_type
        self.color = color
        self.position = position
        self.name = name

    def draw(self):
        if self.shape_type == 'X':
            pygame.draw.line(self.window, self.color, (self.position[0], self.position[1]),
                             (self.position[0] + self.size[0], self.position[1] + self.size[1]), 3)

