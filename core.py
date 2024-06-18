import sys
import time
import pygame
from ui_tools import Label
from frames import MainMenu

class Core:
    """
    The Core class initializes and runs the main game loop for the BreakOut game.
    """
    def __init__(self, width, height, title, icon):
        """
        Initialize the Core class with game window parameters.
        """
        self.window = None
        self.width = width
        self.height = height
        self.title = title
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.active_frame = None
        self.icon = pygame.image.load(icon)

    def initialize(self):
        """
        Initialize Pygame, the mixer for sound, and the game window.
        """
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.set_volume(0.1)
        background_music = 'assets/sound/background_music.mp3'
        pygame.mixer.music.load(background_music)
        pygame.mixer.music.play(-1)

        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        pygame.display.set_icon(self.icon)
        self.active_frame = MainMenu(self.window, self, 0.1)

    def event_handler(self):
        """
        Handle events such as quitting the game and passing events to the active frame.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            self.active_frame.event_handler(event)

    def draw(self):
        """
        Draw the active frame and update the display.
        """
        self.active_frame.draw()
        pygame.display.flip()

    def run(self):
        """
        Run the main game loop, handling events and drawing frames at a set FPS.
        """
        while True:
            self.event_handler()
            self.draw()
            self.clock.tick(self.fps)

if __name__ == '__main__':
    break_out = Core(900, 700, 'BreakOut', 'assets/img/icon.png')
    break_out.initialize()
    break_out.run()
