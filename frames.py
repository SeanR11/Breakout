import json
import random
import sys
import time
import pygame
from ui_tools import *
from game_objects import *


class Frame:
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.static_objects = []
        self.active_objects = []
        self.main_color = (255, 255, 255)
        self.alt_color = (252, 245, 95)
        self.popup_window = None
        self.fx_volume = 0.1
        self.music_volume = 0.3

    def event_handler(self, event):
        if not self.popup_window:
            for active_objects in self.active_objects:
                active_objects.event_handler(event)
        else:
            self.popup_window.event_handler(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.pause_window()

    def draw(self):
        for obj in [*self.static_objects, *self.active_objects]:
            obj.draw()

        if self.popup_window:
            self.popup_window.draw()

    def reset_frame(self):
        self.window.fill((0, 0, 0))

    def load_frame(self, frame):
        self.reset_frame()
        self.parent.active_frame = frame(self.window, self.parent, self.fx_volume)

    def pause_window(self):
        if not self.popup_window:
            self.popup_window = Surface(self.window, self, (300, 200), (0, 0), 'vh', 2)
            self.popup_window.add_object(Label(self.popup_window.surface, self.popup_window, 'PAUSED', 60,
                                               self.main_color, (0, 10), ('h')))
            self.popup_window.add_object(
                Image(self.popup_window.surface, self.popup_window, 'assets/img/sound.jpg', (40, 40), (60, 80),
                      action=lambda: self.turn_music('act')))
            self.popup_window.add_object(
                Image(self.popup_window.surface, self.popup_window, 'assets/img/music.jpg', (40, 40), (200, 80),
                      action=lambda: self.turn_fx('act')))

            self.popup_window.add_object(Button(self.popup_window.surface, self.popup_window, 'resume', 30,
                                                self.main_color, self.alt_color, (30, 150),
                                                action=lambda: self.pause_window()))
            self.popup_window.add_object(Button(self.popup_window.surface, self.popup_window, 'menu', 30,
                                                self.main_color, self.alt_color, (190, 150),
                                                action=lambda: self.load_frame(MainMenu)))
            self.turn_fx('draw')
            self.turn_music('draw')
        else:
            self.popup_window = None
            self.window.fill((0, 0, 0))

    def turn_music(self, mode):
        if pygame.mixer.music.get_busy():
            if mode == 'act':
                pygame.mixer.music.stop()
                self.popup_window.add_object(
                    Shape(self.popup_window.surface, self.popup_window, 'X', 'music_cross', (40, 40), (60, 80),
                          (255, 255, 255)))
        else:
            if mode == 'act':
                background_music = 'assets/sound/background_music.mp3'
                pygame.mixer.music.load(background_music)
                pygame.mixer.music.play(-1)
                for idx, obj in enumerate(self.popup_window.objects):
                    if type(obj) == Shape:
                        if obj.name == 'music_cross':
                            del self.popup_window.objects[idx]
            else:
                self.popup_window.add_object(
                    Shape(self.popup_window.surface, self.popup_window, 'X', 'music_cross', (40, 40), (60, 80),
                          (255, 255, 255)))

    def turn_fx(self, mode):
        if self.fx_volume == 0:
            if mode == 'act':
                self.update_volume(0.3)
                for idx, obj in enumerate(self.popup_window.objects):
                    if type(obj) == Shape:
                        if obj.name == 'fx_cross':
                            del self.popup_window.objects[idx]
            else:
                self.popup_window.add_object(
                    Shape(self.popup_window.surface, self.popup_window, 'X', 'fx_cross', (40, 40), (200, 80),
                          (255, 255, 255)))
        else:
            if mode == 'act':
                self.update_volume(0)
                self.popup_window.add_object(
                    Shape(self.popup_window.surface, self.popup_window, 'X', 'fx_cross', (40, 40), (200, 80),
                          (255, 255, 255)))

    def update_volume(self, volume):
        self.fx_volume = volume
        if self.popup_window:
            self.popup_window.fx_volume = volume


class MainMenu(Frame):
    def __init__(self, window, parent, fx_vol):
        super().__init__(window, parent)
        self.fx_volume = fx_vol

        self.load_ui()

    def load_ui(self):
        # Title
        self.static_objects.append(Image(self.window, self.parent, 'assets/img/logo.png', (700, 300), (100, 0), 'h'))

        # Buttons
        self.active_objects.append(
            Button(self.window, self.parent, 'Start Game', 72, self.main_color, self.alt_color, (0, 350), 'h',
                   lambda: self.load_frame(Game)))
        self.active_objects.append(
            Button(self.window, self.parent, 'Records', 72, self.main_color, self.alt_color, (0, 450), 'h',
                   lambda: self.load_frame(Records)))
        self.active_objects.append(
            Button(self.window, self.parent, 'Exit', 72, self.main_color, self.alt_color, (0, 550), 'h', sys.exit))


class Game(Frame):
    def __init__(self, window, parent, fx_vol):
        super().__init__(window, parent)
        self.lifes = 3
        self.points = 0
        self.game_state = 'run'
        self.levels = {}
        self.records = {}
        self.game_objects = {}
        self.balls = []
        self.blocks = []
        self.rewards = []
        self.popup_window = False

        self.fx_volume = fx_vol
        self.level_over_sound = pygame.mixer.Sound('assets/sound/level_over.wav')
        self.load_ui()

    def event_handler(self, event):
        if self.game_state != 'over':
            super().event_handler(event)
        key = pygame.key.get_pressed()
        if not self.popup_window:
            self.game_objects['player'].event_handler(event)
            if key[pygame.K_ESCAPE]:
                for ball in self.balls:
                    ball.freeze = False
        else:
            self.popup_window.event_handler(event)
            if key[pygame.K_ESCAPE] and self.game_state != 'over':
                self.pause_game()
                for ball in self.balls:
                    ball.freeze = True
            self.popup_window.event_handler(event)

    def draw(self):
        self.window.fill((0, 0, 0))

        self.game_objects['lifes'].draw()
        self.game_objects['points'].draw()
        self.game_objects['game_surface'].draw()

        self.game_logic()
        super().draw()

    def load_ui(self):
        # Data bar
        self.points += 0
        self.static_objects.append(Label(self.window, self.parent, 'Life', 50, self.main_color, (20, 10)))
        self.game_objects['lifes'] = Sprite(self.window, self.parent, (1075, 619, 96, 85), (40, 40), (160, 15),
                                            duplicate=self.lifes)

        self.static_objects.append(Label(self.window, self.parent, 'Points', 50, self.main_color, (550, 10)))
        self.game_objects['points'] = Label(self.window, self.parent, str(self.points), 50, self.main_color,
                                            (850 - 20 * len(str(self.points)), 10))

        # Game
        self.game_objects['game_surface'] = Surface(self.window, self, (845, 615), (30, 70), 'h', 5)
        self.game_objects['player'] = Player(self.game_objects['game_surface'].surface,
                                             self.game_objects['game_surface'], (0, 540), 'h')
        self.balls.append(Ball(self.game_objects['game_surface'].surface, self.game_objects['game_surface']))
        self.game_objects['game_surface'].add_object(self.game_objects['player'])
        self.game_objects['game_surface'].add_object(self.balls[0])

        with open('assets/data.json', mode='r') as data_file:
            data = json.load(data_file)
            self.levels = data['levels']
            self.records = data['records']

        self.window.fill((0, 0, 0))
        self.load_level()

    def game_logic(self):
        for ball_idx, ball in enumerate(self.balls):
            if ball is not None:
                for idx, block in enumerate(self.blocks):
                    if ball.check_brick_collision(block.box):
                        ball.sounds['hit block'].stop()
                        ball.sounds['hit block'].play().set_volume(self.fx_volume)
                        self.update_points(10)
                        if block.hit() or ball.fireball:
                            self.add_reward(15, block.box.midbottom)
                            self.game_objects['game_surface'].remove_object(self.blocks[idx])
                            del self.blocks[idx]
                            if len(self.blocks) == 0:
                                self.reset_game()
                                self.level_over_sound.stop()
                                self.level_over_sound.play().set_volume(self.fx_volume)
                                self.load_level()
                        return
                if ball.check_paddle_collision(self.game_objects['player']):
                    ball.sounds['hit player'].stop()
                    ball.sounds['hit player'].play().set_volume(self.fx_volume)

                if ball.check_brick_collision(pygame.rect.Rect(0, 635, 845, 10)):
                    ball.sounds['drop'].stop()
                    ball.sounds['drop'].play().set_volume(self.fx_volume)
                    if len(self.balls) == 1:
                        self.lifes -= 1
                        if self.lifes != 0:
                            self.game_objects['lifes'].set_duplicate(self.lifes)
                            self.reset_game()
                        else:
                            self.game_over()
                    else:
                        del self.balls[ball_idx]
                        self.game_objects['game_surface'].remove_object(ball)

        for bullet_idx, bullet in enumerate(self.game_objects['player'].bullets):
            for block_idx, block in enumerate(self.blocks):
                if bullet.check_collision(block.box) and len(self.blocks) != 0:
                    del self.game_objects['player'].bullets[bullet_idx]
                    self.update_points(10)
                    if block.hit():
                        self.add_reward(15, block.box.midbottom)
                        self.game_objects['game_surface'].remove_object(self.blocks[block_idx])
                        del self.blocks[block_idx]
                        if len(self.blocks) == 0:
                            self.reset_game()
                            self.level_over_sound.stop()
                            self.level_over_sound.play().set_volume(self.fx_volume)
                            self.load_level()
                    return

        for idx, reward in enumerate(self.rewards):
            if reward.check_collision(self.game_objects['player'].box):
                if reward.name == '+50':
                    self.update_points(50)
                elif reward.name == '+100':
                    self.update_points(100)
                elif reward.name == '+250':
                    self.update_points(250)
                elif reward.name == '+500':
                    self.update_points(500)
                elif reward.name == 'slow':
                    self.game_objects['player'].update_speed(self.game_objects['player'].speed / 2.5)
                elif reward.name == 'fast':
                    self.game_objects['player'].update_speed(self.game_objects['player'].speed * 2.5)
                elif reward.name == '-size':
                    self.game_objects['player'].paddle_size -= 1 if self.game_objects['player'].paddle_size != 0 else 0
                    self.game_objects['player'].update_paddle()
                elif reward.name == '+size':
                    self.game_objects['player'].paddle_size += 1 if self.game_objects['player'].paddle_size != 2 else 2
                    self.game_objects['player'].update_paddle()
                elif reward.name == '+life' and self.lifes < 4:
                    self.lifes += 1
                    self.game_objects['lifes'].set_duplicate(self.lifes)
                elif reward.name == '+ball':
                    new_ball = Ball(self.game_objects['game_surface'].surface, self.game_objects['game_surface'])
                    for ball in self.balls:
                        if ball.fireball:
                            new_ball.fireball = True
                    self.balls.append(new_ball)
                    self.game_objects['game_surface'].add_object(new_ball)
                elif reward.name == 'fireball':
                    for ball in self.balls:
                        ball.active_fireball()
                elif reward.name == 'shooter':
                    self.game_objects['player'].set_shooter()

                del self.rewards[idx]
                self.game_objects['game_surface'].remove_object(reward)

    def load_level(self, level=None):
        self.popup_window = Surface(self.window, self.parent, (300, 150), (0, 0), 'vh', 2)
        self.popup_window.add_object(Label(self.popup_window.surface, self.parent, 'LOADING', 36,
                                           self.main_color,
                                           (0, 55), 'h'))
        self.popup_window.draw()
        pygame.display.flip()
        x, y = (75, 35)
        x_gap = 70
        y_gap = 25
        if level is None:
            level_tup = random.choice(list(self.levels.items()))
            level_data = level_tup[1]
            del self.levels[level_tup[0]]
        else:
            level_data = self.levels[f'level_{level}']
            del self.levels[f'level_{level}']
        for r, row in enumerate(level_data):
            if len(row) == 1:
                row = [row[0] for i in range(10)]
            for c, col in enumerate(row):
                if col != 0:
                    position = ((x + (x_gap * c), y + (y_gap * r)))
                    block = Block(self.game_objects['game_surface'].surface, self.game_objects['game_surface'],
                                  position, col)
                    self.blocks.append(block)
                    self.game_objects['game_surface'].add_object(block)
        self.popup_window = None

    def add_reward(self, chance, position):
        reward_chance = random.randint(1, 100)
        if reward_chance <= chance:
            reward = Reward(self.game_objects['game_surface'].surface,
                            self.game_objects['game_surface'], position=position)
            self.rewards.append(reward)
            self.game_objects['game_surface'].add_object(reward)

    def game_over(self):
        self.game_state = 'over'
        self.pause_game()
        if self.check_record():
            pygame.mixer.Sound('assets/sound/break_record.wav').play().set_volume(self.fx_volume)
            self.popup_window = Surface(self.window, self.parent, (400, 250), (0, 0), 'vh', 2)
            self.popup_window.add_object(Label(self.popup_window.surface, self.popup_window, 'New  record  achieved',
                                               36, self.main_color,
                                               (0, 20), 'h'))
            self.popup_window.add_object(Label(self.popup_window.surface, self.parent,
                                               f'Record              {self.points} Pts', 30,
                                               self.main_color, (0, 69), 'h'))
            self.popup_window.add_object(TextBox(self.popup_window.surface, self.popup_window, 'Enter  name', 20,
                                                 self.main_color, (100, 130), 'h', 15))
            self.popup_window.add_object(Button(self.popup_window.surface, self.popup_window, 'Save', 26,
                                                self.main_color,
                                                self.alt_color, (190, 200),
                                                action=lambda: self.save_record(
                                                    str(*[textbox.text for textbox in self.popup_window.objects if
                                                          type(textbox) == TextBox])),
                                                center='h'))

            self.popup_window.add_object(Button(self.popup_window.surface, self.popup_window, 'again', 26, self.main_color,
                                                self.alt_color, (20, 200), action=lambda: self.load_frame(Game)))
            self.popup_window.add_object(Button(self.popup_window.surface, self.popup_window, 'menu', 26,
                                                self.main_color,
                                                self.alt_color, (320, 200), action=lambda: self.load_frame(MainMenu)))
        else:
            pygame.mixer.Sound('assets/sound/game_over.wav').play().set_volume(self.fx_volume)
            self.popup_window = Surface(self.window, self.parent, (400, 160), (0, 0), 'vh', 1)
            self.popup_window.add_object(Label(self.popup_window.surface, self.parent, 'Game Over', 36,
                                               self.main_color,
                                               (0, 40), 'h'))
            self.popup_window.add_object(Button(self.popup_window.surface, self.popup_window, 'again', 26, self.main_color,
                                                self.alt_color, (20, 115), action=lambda: self.load_frame(Game)))
            self.popup_window.add_object(Button(self.popup_window.surface, self.popup_window, 'menu', 26,
                                                self.main_color,
                                                self.alt_color, (320, 115), action=lambda: self.load_frame(MainMenu)))

    def check_record(self):
        for idx, record in enumerate(self.records):
            if self.points > record[0]:
                record_list = list(self.records[:-1])
                record_list.insert(idx, (self.points, "%ptr%"))
                self.records = record_list
                return True
        return False

    def save_record(self, name):
        saved = False
        for idx, record in enumerate(self.records):
            if '%ptr%' == record[1]:
                self.records[idx] = (record[0], name)
                saved = True
        if saved:
            self.popup_window.add_object(Label(self.popup_window.surface, self.popup_window, 'Saved', 26,
                                               self.alt_color, (190, 200), center='h'))
            with open('assets/data.json', 'r+') as data_file:
                data = json.load(data_file)
                data['records'] = self.records
                data_file.seek(0)
                data_file.write(json.dumps(data, indent=4))

    def pause_game(self):
        if self.popup_window:
            self.popup_window.add_object(Button(self.popup_window.surface, self.popup_window, 'resume', 30,
                                                self.main_color, self.alt_color, (30, 150),
                                                action=lambda: self.pause_game()))
        else:
            for ball in self.balls:
                ball.freeze = False

        if self.game_state == 'over':
            for ball in self.balls:
                ball.freeze = True

    def reset_game(self):
        self.game_objects['player'].reset()
        for idx, ball in enumerate(self.balls):
            self.game_objects['game_surface'].remove_object(ball)
            del self.balls[idx]
        self.balls.append(Ball(self.game_objects['game_surface'].surface, self.game_objects['game_surface']))
        self.balls[0].reset()
        self.game_objects['game_surface'].add_object(self.balls[0])

        while len(self.rewards):
            self.game_objects['game_surface'].remove_object(self.rewards[0])
            del self.rewards[0]

    def update_points(self, points):
        self.points += points
        self.game_objects['points'] = Label(self.window, self.parent, str(self.points), 50, self.main_color,
                                            (850 - 20 * len(str(self.points)), 10))


class Records(Frame):
    def __init__(self, window, parent, fx_vol):
        super().__init__(window, parent)
        self.records = []
        self.load_ui()

    def load_ui(self):
        # Title
        self.static_objects.append(Label(self.window, self.parent, 'Records', 90, self.main_color, (0, 50), 'h'))

        # Load records from JSON
        with open('assets/data.json', mode='r') as data_file:
            data = json.load(data_file)
            self.records = data['records']

        # Display records
        record_spacing = 80
        for idx, record in enumerate(self.records):
            y_offset = 160 + idx * record_spacing
            self.static_objects.append(Label(self.window, self.parent, f'{idx + 1}', 60, self.main_color, (100, y_offset)))
            self.static_objects.append(Label(self.window, self.parent, f' {record[1]}', 60, self.main_color, (150, y_offset)))
            self.static_objects.append(Label(self.window, self.parent, f'{record[0]}', 60, self.main_color, (670, y_offset)))

        # Back button
        self.active_objects.append(Button(self.window, self.parent, 'back', 70, self.main_color, self.alt_color, (0, 600), 'h',
                                         action=lambda: self.load_frame(MainMenu)))
