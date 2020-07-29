import sys
import random
from abc import ABC, abstractmethod

import pygame

images = {
    'bg': './assets/bg.png',
    'bird': './assets/bird.png',
    'pipe': './assets/pipe.png',
    'ground': './assets/ground.png'
}

pygame.font.init()
font = pygame.font.SysFont(None, 48)

FPS = 60
FAST_FORWARD = 1

WIN_WIDTH, WIN_HEIGHT = 300, 400
GND_HEIGHT = 60
MOVE_SPEED = 2


class BaseSprite(ABC):
    def __init__(self, img_src):
        self.x = self.y = 0
        self.image = pygame.image.load(img_src).convert_alpha()
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def get_rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))

    def get_mask(self):
        return pygame.mask.from_surface(self.image)

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def render(self, surface):
        pass


class Bird(BaseSprite):
    FLAP_V = -8
    DELTA_V = 0.5

    v = 0
    alive = True

    def __init__(self):
        super().__init__(images['bird'])
        # centering
        rect = self.get_rect()
        self.x = (WIN_WIDTH - rect.width) / 2
        self.y = (WIN_HEIGHT - rect.height) / 2

    def flap(self):
        self.v = self.FLAP_V

    def is_alive(self, pipe_pair):
        if not self.alive:
            return False
        self.alive = self.y + self.height < WIN_HEIGHT - GND_HEIGHT and \
                     not self.collide(pipe_pair)
        return self.alive

    def collide(self, pipe_pair):
        top = pipe_pair.top
        bottom = pipe_pair.bottom
        bird_mask = self.get_mask()
        top_mask = top.get_mask()
        bottom_mask = bottom.get_mask()
        top_offset = (int(top.x - self.x), int(top.y - self.y))
        bottom_offset = (int(bottom.x - self.x), int(bottom.y - self.y))

        return bird_mask.overlap(top_mask, top_offset) or \
               bird_mask.overlap(bottom_mask, bottom_offset)

    def update(self):
        self.y += self.v
        self.v += self.DELTA_V

    def render(self, surface):
        angle = min(self.v / self.FLAP_V * 45, 90)
        rot_img = pygame.transform.rotate(self.image, angle)
        rot_rect = rot_img.get_rect(center=self.get_rect().center)
        surface.blit(rot_img, rot_rect)


class Ground(BaseSprite):
    def __init__(self):
        super().__init__(images['ground'])
        self.x = 0
        self.y = WIN_HEIGHT - GND_HEIGHT

    def update(self):
        self.x = self.x - MOVE_SPEED
        if self.x <= -self.width:
            self.x = 0

    def render(self, surface):
        x = self.x
        while x <= WIN_WIDTH:
            surface.blit(self.image, (x, self.y))
            x += self.width


class Pipe(BaseSprite):
    def __init__(self, x, y, flip=False):
        super().__init__(images['pipe'])
        self.x = x
        self.y = y
        if flip:
            self.image = pygame.transform.flip(self.image, False, True)

    def update(self):
        self.x -= MOVE_SPEED

    def render(self, surface):
        surface.blit(self.image, (self.x, self.y))


class PipePair:
    GAP_HEIGHT = 100

    @property
    def x(self):
        return self.top.x

    @property
    def x_max(self):
        return self.top.x + self.width

    @property
    def midpoint(self):
        return self.x + self.width / 2, \
               (self.top.y + self.bottom.y) / 2

    def __init__(self, x):
        bottom_y = random.randint(
            self.GAP_HEIGHT + 50,
            WIN_HEIGHT - GND_HEIGHT - 50
        )
        self.bottom = Pipe(x, bottom_y)
        self.top = Pipe(
            x, bottom_y - self.GAP_HEIGHT - self.bottom.height,
            True
        )
        self.width = self.top.width
        self.height = self.top.height

    def update(self):
        self.bottom.update()
        self.top.update()

    def render(self, surface):
        self.bottom.render(surface)
        self.top.render(surface)


class Game:
    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    bg_img = pygame.transform.scale(
        pygame.image.load(images['bg']).convert_alpha(),
        (WIN_WIDTH, WIN_HEIGHT - GND_HEIGHT)
    )

    def __init__(self):
        self.pipes = [PipePair(WIN_WIDTH)]
        self.bird = Bird()
        self.ground = Ground()
        self.frontier = self.pipes[0]
        pygame.display.set_caption('Flappy Bird')

    def flush_pipes(self):
        if self.frontier.x_max <= self.bird.x:
            pipe = PipePair(WIN_WIDTH)
            self.pipes.append(pipe)
            self.frontier = pipe

        if self.pipes[0].x_max <= 0:
            self.pipes.pop(0)

    def update(self):
        self.bird.update()
        self.ground.update()
        for p in self.pipes:
            p.update()
        self.flush_pipes()

    def render(self):
        surface = self.screen
        surface.blit(self.bg_img, (0, 0))
        for p in self.pipes:
            p.render(surface)
        self.ground.render(surface)
        self.bird.render(surface)

        if self.bird.collide(self.frontier):
            img = font.render('COLLIDED', True, (255, 255, 255))
            surface.blit(img, (10, 10))

    def start(self):
        clock = pygame.time.Clock()
        while True:
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    sys.exit()
                if evt.type == pygame.KEYDOWN and \
                   evt.key == pygame.K_SPACE:
                    game.bird.flap()
            for _ in range(FAST_FORWARD):
                self.update()
            self.render()
            pygame.display.update()
            clock.tick(FPS)


if __name__ == '__main__':
    game = Game()
    game.start()
