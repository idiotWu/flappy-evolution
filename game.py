from __future__ import annotations

import sys
import random
from abc import ABC, abstractmethod
from typing import List, Tuple

import pygame

images = {
    'bg': './assets/bg.png',
    'bird': './assets/bird.png',
    'pipe': './assets/pipe.png',
    'ground': './assets/ground.png'
}

pygame.font.init()
font = pygame.font.SysFont('arialttf, arial', 20)

FPS = 60

WIN_WIDTH, WIN_HEIGHT = 400, 500
GND_HEIGHT = 60
MOVE_SPEED = 3


class BaseSprite(ABC):
    image: pygame.Surface
    width: int
    height: int
    x: float
    y: float

    def __init__(self, img_src: str):
        self.x = self.y = 0
        self.image = pygame.image.load(img_src).convert_alpha()
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def get_rect(self) -> pygame.Rect:
        return self.image.get_rect(topleft=(self.x, self.y))

    def get_mask(self) -> pygame.Mask:
        return pygame.mask.from_surface(self.image)

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def render(self, surface: pygame.Surface):
        pass


class Bird(BaseSprite):
    FLAP_V = -8
    DELTA_V = 0.5

    v: float = 0
    alive: bool = True
    score: int

    def __init__(self):
        super().__init__(images['bird'])
        # centering
        rect = self.get_rect()
        self.x = (WIN_WIDTH - rect.width) / 2
        self.y = (WIN_HEIGHT - rect.height) / 2

    def flap(self):
        self.v = self.FLAP_V

    def check_alive(self, pipe_pair: PipePair) -> bool:
        if not self.alive:
            return False
        self.alive = self.y > -self.height and \
                     self.y + self.height < WIN_HEIGHT - GND_HEIGHT and \
                     not self.collide(pipe_pair)
        return self.alive

    def collide(self, pipe_pair: PipePair):
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

    def render(self, surface: pygame.Surface):
        angle = min(self.v / self.FLAP_V * 45, 90)
        rot_img = pygame.transform.rotate(self.image, angle)
        rot_rect = rot_img.get_rect(center=self.get_rect().center)
        surface.blit(rot_img, rot_rect)

    def get_offset(self, pipe_pair: PipePair) -> Tuple[float, float]:
        midpoint = pipe_pair.midpoint
        x = (midpoint[0] - self.x) / WIN_WIDTH
        y = (midpoint[1] - self.y) / WIN_HEIGHT
        return x, y


class Ground(BaseSprite):
    def __init__(self):
        super().__init__(images['ground'])
        self.x = 0
        self.y = WIN_HEIGHT - GND_HEIGHT

    def update(self):
        self.x = self.x - MOVE_SPEED
        if self.x <= -self.width:
            self.x = 0

    def render(self, surface: pygame.Surface):
        x = self.x
        while x <= WIN_WIDTH:
            surface.blit(self.image, (x, self.y))
            x += self.width


class Pipe(BaseSprite):
    def __init__(self, x: float, y: float, flip=False):
        super().__init__(images['pipe'])
        self.x = x
        self.y = y
        if flip:
            self.image = pygame.transform.flip(self.image, False, True)

    def update(self):
        self.x -= MOVE_SPEED

    def render(self, surface: pygame.Surface):
        surface.blit(self.image, (self.x, self.y))


class PipePair:
    GAP_HEIGHT = 100

    @property
    def x(self) -> float:
        return self.top.x

    @property
    def x_max(self) -> float:
        return self.top.x + self.width

    @property
    def midpoint(self) -> Tuple[float, float]:
        return self.x + self.width / 2, \
               (self.top.y + self.bottom.y) / 2

    def __init__(self, x: float):
        bottom_y = random.randint(
            self.GAP_HEIGHT + 20,
            WIN_HEIGHT - GND_HEIGHT - 20
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

    def render(self, surface: pygame.Surface):
        self.bottom.render(surface)
        self.top.render(surface)


class Game:
    screen: pygame.Surface = pygame.display.set_mode(
        (WIN_WIDTH, WIN_HEIGHT)
    )

    bg_img: pygame.Surface = pygame.transform.scale(
        pygame.image.load(images['bg']).convert_alpha(),
        (WIN_WIDTH, WIN_HEIGHT - GND_HEIGHT)
    )

    fast_forward: int = 1

    score: int = 0
    max_score: int = 0

    birds: List[Bird]
    pipes: List[PipePair]
    ground: Ground
    frontier: PipePair

    bird_count: int

    def __init__(self, bird_count=50):
        pygame.display.set_caption('Flappy Bird')
        self.bird_count = bird_count
        self.reset()

    def reset(self):
        self.score = 0
        self.pipes = [PipePair(WIN_WIDTH)]
        self.birds = [Bird() for _ in range(self.bird_count)]
        self.ground = Ground()
        self.frontier = self.pipes[0]

    def flush_pipes(self):
        if self.frontier.x_max <= self.birds[0].x:
            pipe = PipePair(WIN_WIDTH)
            self.pipes.append(pipe)
            self.frontier = pipe

        if self.pipes[0].x_max <= 0:
            self.pipes.pop(0)

    def update(self):
        self.score += 1
        self.max_score = max(self.max_score, self.score)
        for pipe in self.pipes:
            pipe.update()
        for bird in self.birds:
            if bird.check_alive(self.frontier):
                bird.score = self.score
                bird.update()
        self.ground.update()
        self.flush_pipes()

    def render(self):
        surface = self.screen
        surface.blit(self.bg_img, (0, 0))
        for pipe in self.pipes:
            pipe.render(surface)
        for bird in self.birds:
            if bird.alive:
                bird.render(surface)
        self.ground.render(surface)

    def draw_text(self, text: str, x: int, y: int):
        img = font.render(text, True, (255, 255, 255))
        self.screen.blit(img, (x, y))

    def change_speed(self, delta: int):
        ff = self.fast_forward + delta
        self.fast_forward = min(10, max(1, ff))

    def start(self):
        pygame.key.set_repeat(100, 100)
        clock = pygame.time.Clock()
        while True:
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    sys.exit()
                if evt.type == pygame.KEYDOWN:
                    if evt.key == pygame.K_UP:
                        self.change_speed(1)
                    if evt.key == pygame.K_DOWN:
                        self.change_speed(-1)

            for _ in range(self.fast_forward):
                self.update()

            self.render()
            pygame.display.update()
            clock.tick(FPS)


if __name__ == '__main__':
    Game().start()
