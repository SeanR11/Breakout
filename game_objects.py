import random
import math
import pygame
import time
from ui_tools import Sprite


class Player(Sprite):
    def __init__(self, window, parent, position,center=''):
        super().__init__(window, parent, (530, 23, 202, 53), (100, 30), position)
        self.bounds = self.window.get_rect()
        self.paddle_size = 1
        self.speed = 9
        self.speed_limits = [self.speed/2.5,self.speed*2.5]
        self.move_state = False
        self.shooter = False
        self.shooter_cd = 1
        self.shooter_timer = None
        self.bullets_amount = 0
        self.bullets_sprite = None
        self.bullets = []
        if center:
            self.set_center(center)

    def event_handler(self, event):
        super().event_handler(event)
        key = pygame.key.get_pressed()
        if key[pygame.K_RIGHT] or key[pygame.K_LEFT]:
            self.move_state = True
        else:
            self.move_state = False

    def draw(self):
        super().draw()
        if self.move_state:
            self.move(pygame.key.get_pressed())
        if self.shooter:
            self.bullets_sprite.draw()
            for idx,bullet in enumerate(self.bullets):
                bullet.draw()

            if self.shooter_timer and time.time() - self.shooter_timer >= self.shooter_cd:
                self.shooter_timer = None

    def move(self, key):
        if key[pygame.K_RIGHT] and self.box.right + 10 < self.bounds.w:
            self.box.x += self.speed
        if key[pygame.K_LEFT] and self.box.left - 3 > self.bounds.x:
            self.box.x -= self.speed

    def shoot(self):
        if self.bullets_amount != 0:
            bullet = Bullet(self.window, self.parent, (0, 0))
            bullet.update_position((self.box.centerx - bullet.box.w, self.box.y - 1))
            self.bullets.append(Bullet(self.window, self.parent, (self.box.centerx, self.box.top - 20)))
            self.update_magazine()
            self.shooter_timer = time.time()
            return True
        return False

    def set_shooter(self):
        self.shooter = True
        self.bullets_amount = 5
        self.bullets_sprite = Sprite(self.window,self.parent,(1116,856,14,31),(10,20),(700,575),duplicate=self.bullets_amount)

    def update_magazine(self):
        self.bullets_amount -= 1
        self.bullets_sprite.set_duplicate(self.bullets_amount)

    def update_speed(self,speed):
        if self.speed_limits[0] <= speed <= self.speed_limits[1]:
            self.speed = speed

    def update_paddle(self):
        if self.paddle_size == 0:
                self.update_sprite((985, 870, 96, 53), (50, 30))
        elif self.paddle_size == 1:
            self.update_sprite((530, 23, 202, 53), (100, 30))
        elif self.paddle_size == 2:
            self.update_sprite((758, 499, 290, 53), (175, 30))

    def reset(self):
        self.update_position((0, 540),'h')
        self.paddle_size = 1
        self.update_paddle()
        self.speed = 9
        self.shooter = False
        self.bullets = []


class Ball(Sprite):
    def __init__(self, window, parent,):
        super().__init__(window, parent, (1075, 732, 97, 96), (20, 20), (0, 0))
        self.speed = 4.5
        self.freeze = False
        self.fireball = False
        self.fireball_mask = None
        self.fireball_timer = None
        self.fireball_stages = [(1216,24,452,109),(1216,157,501,114),(1217,304,522,102),(1216,423,516,103)]
        self.fireball_stage = 0
        self.fireball_animation_angle = 0
        self.fireball_animation_timer = False
        self.fireball_animation_rate = 0.1
        self.dx = self.speed
        self.dy = -self.speed
        self.update_position((0, 500),'h')
        self.x, self.y = self.box.topleft
        self.bounds = self.window.get_rect()
        self.sounds = {
            'hit player': pygame.mixer.Sound('assets/sound/ball_player.wav'),
            'hit wall': pygame.mixer.Sound('assets/sound/ball_wall.wav'),
            'hit block': pygame.mixer.Sound('assets/sound/ball_block.wav'),
            'drop': pygame.mixer.Sound('assets/sound/ball_drop.wav')
        }


    def draw(self):
        if self.fireball:
            self.fireball_mask.draw()
            if time.time() - self.fireball_timer >= 15:
                self.deactive_fireball()

        super().draw()
        if not self.freeze:
            self.move()

    def move(self):
        if self.box.x + self.box.w > self.bounds.width or self.box.x < self.bounds.x:
            self.sounds['hit wall'].stop()
            self.sounds['hit wall'].play().set_volume(self.parent.parent.fx_volume)
            self.dx *= -1
        if self.box.y < self.bounds.y:
            self.sounds['hit wall'].stop()
            self.sounds['hit wall'].play().set_volume(self.parent.parent.fx_volume)
            self.dy *= -1
        self.x += self.dx
        self.y += self.dy
        self.update_position((self.x, self.y))
        if self.fireball:
            self.update_fireball_animation()

    def update_speed(self, speed):
        self.speed = speed
        self.dx = self.speed if self.dx > 0 else -self.speed
        self.dy = self.speed if self.dy > 0 else -self.speed

    def check_brick_collision(self, object_rect):
        collision_detected = False

        # Determine overlap amounts
        overlap_left = self.box.right - object_rect.left
        overlap_right = object_rect.right - self.box.left
        overlap_top = self.box.bottom - object_rect.top
        overlap_bottom = object_rect.bottom - self.box.top

        # Find the smallest overlap
        smallest_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

        # Adjust ball direction based on the smallest overlap
        if self.box.colliderect(object_rect):
            collision_detected = True
            if self.fireball:
                return True
            if smallest_overlap == overlap_left:
                self.dx = -abs(self.dx)
                self.box.right = object_rect.left  # Adjust position to avoid sticking
            elif smallest_overlap == overlap_right:
                self.dx = abs(self.dx)
                self.box.left = object_rect.right  # Adjust position to avoid sticking
            elif smallest_overlap == overlap_top:
                self.dy = -abs(self.dy)
                self.box.bottom = object_rect.top  # Adjust position to avoid sticking
            elif smallest_overlap == overlap_bottom:
                self.dy = abs(self.dy)
                self.box.top = object_rect.bottom  # Adjust position to avoid sticking

        return collision_detected

    def check_paddle_collision(self, object_rect):
        collision_detected = False
        if self.box.colliderect(object_rect):
            collision_detected = True
            offset = (self.box.centerx - object_rect.left) / 100
            flag = 0
            if offset > 0.5 :
                offset = -1 - (offset - 0.5) * -2
            else:
                offset = offset * 2
                flag = 1
            angle = offset * 90
            min_angle = 30
            if offset > 0 and angle < min_angle:
                angle = min_angle
            elif offset < 0 and angle > -min_angle:
                angle = -min_angle
            radians = math.radians(angle)

            if flag == 1:
                self.dy = self.speed * -math.sin(radians)
                self.dx = self.speed * -math.cos(radians)
            else:
                self.dy = self.speed * math.sin(radians)
                self.dx = self.speed * math.cos(radians)

            speed_magnitude = math.sqrt(self.dx ** 2 + self.dy ** 2)
            self.dx = (self.dx / speed_magnitude*1.5) * self.speed
            self.dy = (self.dy / speed_magnitude*1.5) * self.speed
        return collision_detected

    def reset(self):
        self.dx = self.speed
        self.dy = -self.speed
        self.update_position((0, 500),'h')
        self.x, self.y = self.box.topleft

    def active_fireball(self):
        self.fireball_mask = Sprite(self.window,self.parent,(1216,24,452,109),(50,20),(0,0),center='h')
        self.fireball_animation_timer = time.time()
        self.fireball_timer = time.time()
        self.fireball = True

    def deactive_fireball(self):
        self.fireball_mask = None
        self.fireball_animation_timer = None
        self.fireball = False

    def update_fireball_animation(self):
        if self.fireball_animation_timer and time.time() - self.fireball_animation_timer >= self.fireball_animation_rate:
            if self.fireball_stage >= len(self.fireball_stages) - 1:
                self.fireball_stage = 0
            self.fireball_stage += 1
            self.fireball_mask.update_sprite(self.fireball_stages[self.fireball_stage],size = (50,20),rotation=self.fireball_animation_angle)
            self.fireball_animation_timer = time.time()

        if self.dx > 0 and self.dy < 0:
            self.fireball_animation_angle = 225
            self.fireball_mask.update_position((self.x-33,self.y+8))
        elif self.dx < 0 and self.dy < 0:
            self.fireball_animation_angle = 315
            self.fireball_mask.update_position((self.x+6,self.y+4))
        elif self.dx > 0 and self.dy > 0:
            self.fireball_animation_angle = 135
            self.fireball_mask.update_position((self.x-36,self.y-34))
        elif self.dx < 0 and self.dy > 0:
            self.fireball_animation_angle = 45
            self.fireball_mask.update_position((self.x+5,self.y-35))
        elif self.dx == 0 and self.dy > 0:
            self.fireball_animation_angle = 90
            self.fireball_mask.update_position((self.x,self.y-40))
        elif self.dx == 0 and self.dy < 0:
            self.fireball_animation_angle = 270
            self.fireball_mask.update_position((self.x+2, self.y+15))


class Block(Sprite):
    def __init__(self, window, parent, position, stamina):
        super().__init__(window, parent, (26, 23 + (101 * (stamina - 1)), 227, 75), (70, 25), position)
        self.stamina = stamina

    def hit(self):
        self.stamina -= 1
        if self.stamina == 0:
            return True
        self.update_sprite((26, 23 + (101 * (self.stamina - 1)), 227, 75))
        return False


class Reward(Sprite):
    def __init__(self,window,parent,position):
        sprite_map = {
            '+50': (531,181,203,54),
            '+100': (760, 181, 203, 54),
            '+250': (988, 185, 203, 54),
            '+500': (529, 262, 203, 54),
            'slow': (757, 261, 203, 54),
            'fast': (988, 262, 203, 54),
            '+ball': (529, 341, 203, 54),
            'fireball': (756, 341, 203, 54),
            '-size': (531, 420, 203, 54),
            '+size': (758, 420, 203, 54),
            'shooter': (986, 420, 203, 54),
            '+life': (531,499,204,54)
        }
        reward = random.choice(list(sprite_map.items()))
        self.sprite = reward[1]
        self.name = reward[0]
        super().__init__(window,parent,self.sprite,(70,20),(0,0))
        self.box.midtop = position

        self.y = self.box.y
        self.speed = 3
        self.freeze = False

    def draw(self):
        if not self.freeze:
            self.move()
        super().draw()

    def move(self):
        self.y += self.speed
        self.update_position((self.box.x, self.y))

    def check_collision(self,objet_rect):
        if self.box.colliderect(objet_rect):
            return True
        else:
            return False

class Bullet(Sprite):
    def __init__(self,window,parent,position):
        super().__init__(window,parent,(1116,856,14,31),(10,20),position)
        self.y = self.box.y
        self.speed = 4
        self.sound = pygame.mixer.Sound('assets/sound/shot.wav')
        self.sound.play().set_volume(self.parent.parent.fx_volume)

    def draw(self):
        self.move()
        super().draw()

    def move(self):
        self.y -= self.speed
        self.box.y = self.y

    def check_collision(self, objet_rect):
        if self.box.colliderect(objet_rect):
            return True
        else:
            return False
