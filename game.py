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
GAP_HEIGHT = 150
MIN_PIPE_HEIGHT = 30

GND_V = 3
MAX_PIPE_V = 3
FLAP_V = -8
DELTA_V = 0.6


class BaseSprite(ABC):
    image: pygame.Surface
    width: int
    height: int
    x: float
    y: float

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.height

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
        self.v = FLAP_V

    def check_alive(self, pipe_pair: PipePair) -> bool:
        if not self.alive:
            return False
        self.alive = self.y > -self.height and \
                     self.y + self.height < WIN_HEIGHT - GND_HEIGHT and \
                     not self.collide(pipe_pair)
        return self.alive

    def collide(self, pipe_pair: PipePair):
        if self.right < pipe_pair.left or \
           self.left > pipe_pair.right:
            return False

        return self.top <= pipe_pair.top_pipe.bottom or \
               self.bottom >= pipe_pair.bottom_pipe.top

    def update(self):
        self.y += self.v
        self.v += DELTA_V

    def render(self, surface: pygame.Surface):
        angle = min(self.v / FLAP_V * 45, 90)
        rot_img = pygame.transform.rotate(self.image, angle)
        rot_rect = rot_img.get_rect(center=self.get_rect().center)
        surface.blit(rot_img, rot_rect)

    def get_offset(self, pipe_pair: PipePair) -> Tuple[float, float]:
        mid_x, mid_y = pipe_pair.midpoint
        x = (mid_x - self.x) / WIN_WIDTH
        y = (mid_y - self.y) / WIN_HEIGHT
        return x, y


class Ground(BaseSprite):
    def __init__(self):
        super().__init__(images['ground'])
        self.x = 0
        self.y = WIN_HEIGHT - GND_HEIGHT

    def update(self):
        self.x = self.x - GND_V
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
        self.x -= GND_V

    def render(self, surface: pygame.Surface):
        surface.blit(self.image, (self.x, self.y))


class PipePair:
    top_pipe: Pipe
    bottom_pipe: Pipe
    move_v: int

    @property
    def x(self) -> float:
        return self.top_pipe.x

    @property
    def width(self) -> int:
        return self.top_pipe.width

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def midpoint(self) -> Tuple[float, float]:
        return (
            self.x + self.width / 2,
            (self.top_pipe.bottom + self.bottom_pipe.top) / 2
        )

    def __init__(self, x: float):
        bottom_y = random.randint(
            GAP_HEIGHT + MIN_PIPE_HEIGHT,
            WIN_HEIGHT - GND_HEIGHT - MIN_PIPE_HEIGHT
        )
        self.bottom_pipe = Pipe(x, bottom_y)
        top_y = bottom_y - GAP_HEIGHT - self.bottom_pipe.height
        self.top_pipe = Pipe(x, top_y, True)
        self.move_v = random.randint(1, MAX_PIPE_V)

    def move(self):
        if self.move_v > 0:
            if self.bottom_pipe.top < WIN_HEIGHT - GND_HEIGHT - MIN_PIPE_HEIGHT:
                self.bottom_pipe.y += self.move_v
                self.top_pipe.y += self.move_v
            else:
                self.move_v *= -1
        else:
            if self.top_pipe.bottom > MIN_PIPE_HEIGHT:
                self.bottom_pipe.y += self.move_v
                self.top_pipe.y += self.move_v
            else:
                self.move_v *= -1

    def update(self):
        self.move()
        self.bottom_pipe.update()
        self.top_pipe.update()

    def render(self, surface: pygame.Surface):
        self.bottom_pipe.render(surface)
        self.top_pipe.render(surface)


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
    remain_birds: int

    def __init__(self, bird_count=50):
        pygame.display.set_caption('Flappy Bird')
        self.bird_count = self.remain_birds = bird_count
        self.reset()

    def reset(self):
        self.score = 0
        self.pipes = [PipePair(WIN_WIDTH)]
        self.birds = [Bird() for _ in range(self.bird_count)]
        self.ground = Ground()
        self.frontier = self.pipes[0]

    def calc_remain(self):
        count = 0
        for bird in self.birds:
            if bird.alive:
                count += 1
        self.remain_birds = count

    def flush_pipes(self):
        if self.frontier.right <= self.birds[0].left:
            pipe = PipePair(WIN_WIDTH)
            self.pipes.append(pipe)
            self.frontier = pipe

        if self.pipes[0].right <= 0:
            self.pipes.pop(0)

    def update(self):
        self.score += 1
        self.max_score = max(self.max_score, self.score)
        for pipe in self.pipes:
            pipe.update()
        self.flush_pipes()
        for bird in self.birds:
            if bird.check_alive(self.frontier):
                bird.score = self.score
                bird.update()
        self.calc_remain()
        self.ground.update()

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
        self.fast_forward = max(1, self.fast_forward + delta)

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
                    elif evt.key == pygame.K_RIGHT:
                        self.change_speed(10)
                    elif evt.key == pygame.K_DOWN:
                        self.change_speed(-1)
                    elif evt.key == pygame.K_LEFT:
                        self.change_speed(-10)
                    elif evt.key == pygame.K_ESCAPE:
                        self.fast_forward = 1

            for _ in range(self.fast_forward):
                self.update()

            self.render()
            pygame.display.update()
            clock.tick(FPS)


if __name__ == '__main__':
    Game().start()
