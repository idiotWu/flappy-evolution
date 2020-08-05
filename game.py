from __future__ import annotations

import sys
import random
from abc import ABC, abstractmethod
from typing import List, Tuple

import pygame

# 画像ファイル
images = {
    'bg': './assets/bg.png',
    'bird': './assets/bird.png',
    'pipe': './assets/pipe.png',
    'ground': './assets/ground.png'
}

# フォントを設定する
pygame.font.init()
font = pygame.font.SysFont('arialttf, arial', 20)

# ゲームの FPS
# 高ければ高いほど進行速度が早い
FPS = 60

# ウィンドウのサイズ
WIN_WIDTH, WIN_HEIGHT = 400, 500
# 地面の高さ
GND_HEIGHT = 60
# 土管の隙間の高さ
# 土管の動く速度に応じて調整する必要がある
GAP_HEIGHT = 125
# 土管の最低高さ
MIN_PIPE_HEIGHT = 30

# 地面の移動速度
GND_V = 3
# 土管が動く最大速度
# この速度が速すぎるとゲームが遊べなくなる可能性がある
MAX_PIPE_V = 2
# 小鳥を飛ばすときの速度
FLAP_V = -8
# 小鳥の速度の減衰量
DELTA_V = 0.6


class BaseSprite(ABC):
    """
    スプライトの基底クラス
    """
    # 画像オブジェクト
    image: pygame.Surface
    # 幅
    width: int
    # 高さ
    height: int
    # 位置
    x: float
    y: float

    @property
    def left(self):
        """左側の位置を取得する"""
        return self.x

    @property
    def right(self):
        """右側の位置を取得する"""
        return self.x + self.width

    @property
    def top(self):
        """上側の位置を取得する"""
        return self.y

    @property
    def bottom(self):
        """下側の位置を取得する"""
        return self.y + self.height

    def __init__(self, img_src: str):
        """
        スプライトを生成する．

        Args:
            img_src: 画像ファイルのパス
        """
        self.x = self.y = 0
        self.image = pygame.image.load(img_src).convert_alpha()
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def get_rect(self) -> pygame.Rect:
        """自身の矩形オブジェクトを取得する"""
        return self.image.get_rect(topleft=(self.x, self.y))

    @abstractmethod
    def update(self):
        """自分を更新する"""
        pass

    @abstractmethod
    def render(self, surface: pygame.Surface):
        """
        指定のサーフィスで自分を描画する

        Args:
            surface: 目標のサーフィス
        """
        pass


class Bird(BaseSprite):
    """小鳥のスプライト"""
    # 現在の速度
    v: float = 0
    # 生きているかどうか
    alive: bool = True
    # 得点
    score: int

    def __init__(self):
        super().__init__(images['bird'])
        # 画面中央に置く
        rect = self.get_rect()
        self.x = (WIN_WIDTH - rect.width) / 2
        self.y = (WIN_HEIGHT - rect.height) / 2

    def flap(self):
        """自分を飛ばす"""
        self.v = FLAP_V

    def check_alive(self, pipe_pair: PipePair) -> bool:
        """
        生きているかどうかをチェックする

        Args:
            pipe_pair: 土管対

        Returns: 生きているならば True，そうでなければ False
        """
        if not self.alive:
            return False
        self.alive = self.y > -self.height and \
                     self.y + self.height < WIN_HEIGHT - GND_HEIGHT and \
                     not self.collide(pipe_pair)
        return self.alive

    def collide(self, pipe_pair: PipePair):
        """
        土管対に衝突したかどうかをチェック

        Args:
            pipe_pair: 土管対

        Returns: 衝突したならば True，そうでなければ False
        """
        if self.right < pipe_pair.left or \
           self.left > pipe_pair.right:
            return False

        return self.top <= pipe_pair.top_pipe.bottom or \
               self.bottom >= pipe_pair.bottom_pipe.top

    def update(self):
        self.y += self.v
        self.v += DELTA_V

    def render(self, surface: pygame.Surface):
        # 速度に応じて回転角度を算出する
        angle = min(self.v / FLAP_V * 45, 90)
        # 回転した小鳥を描画する
        rot_img = pygame.transform.rotate(self.image, angle)
        rot_rect = rot_img.get_rect(center=self.get_rect().center)
        surface.blit(rot_img, rot_rect)

    def normalize_offset(self, pipe_pair: PipePair) -> Tuple[float, float]:
        """
        土管対の隙間の中央点との距離を算出し正規化する

        Args:
            pipe_pair: 土管対

        Returns: (offset_x, offset_y)
        """
        mid_x, mid_y = pipe_pair.midpoint
        x = (mid_x - self.x) / WIN_WIDTH
        y = (mid_y - self.y) / WIN_HEIGHT
        return x, y


class Ground(BaseSprite):
    """地面のスプライト"""
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
        # 横方向にリピートする
        while x <= WIN_WIDTH:
            surface.blit(self.image, (x, self.y))
            x += self.width


class Pipe(BaseSprite):
    def __init__(self, x: float, y: float, flip=False):
        """
        指定の位置で土管のスプライトを初期化する

        Args:
            x: X 座標
            y: Y 座標
            flip: 反転するかどうか（上部の土管は反転する）
        """
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
    # 上部の土管
    top_pipe: Pipe
    # 下部の土管
    bottom_pipe: Pipe
    # 垂直方向に動く速度
    v: float

    @property
    def x(self) -> float:
        """X 座標を取得する"""
        return self.top_pipe.x

    @property
    def width(self) -> int:
        """幅を取得する"""
        return self.top_pipe.width

    @property
    def left(self) -> float:
        """左側の位置を取得する"""
        return self.x

    @property
    def right(self) -> float:
        """右側の位置を取得する"""
        return self.x + self.width

    @property
    def midpoint(self) -> Tuple[float, float]:
        """隙間の中央点の座標を取得する"""
        return (
            self.x + self.width / 2,
            (self.top_pipe.bottom + self.bottom_pipe.top) / 2
        )

    def __init__(self, x: float):
        # 下部の頂点はランダム的に決める
        bottom_y = random.randint(
            GAP_HEIGHT + MIN_PIPE_HEIGHT,
            WIN_HEIGHT - GND_HEIGHT - MIN_PIPE_HEIGHT
        )
        self.bottom_pipe = Pipe(x, bottom_y)
        # 下部の頂点により上部の底辺位置を算出する
        top_y = bottom_y - GAP_HEIGHT - self.bottom_pipe.height
        self.top_pipe = Pipe(x, top_y, True)
        # 垂直方向に動く速度をランダム的に決める
        self.v = random.uniform(0, MAX_PIPE_V)

    def move(self):
        """土管対を垂直方向に動かせる"""
        if self.v > 0:
            if self.bottom_pipe.top < WIN_HEIGHT - GND_HEIGHT - MIN_PIPE_HEIGHT:
                self.bottom_pipe.y += self.v
                self.top_pipe.y += self.v
            else:
                # 下部の限界に着いたら速度を反転する
                self.v *= -1
        else:
            if self.top_pipe.bottom > MIN_PIPE_HEIGHT:
                self.bottom_pipe.y += self.v
                self.top_pipe.y += self.v
            else:
                # 上部の限界に着いたら速度を反転する
                self.v *= -1

    def update(self):
        """自分を更新する"""
        self.move()
        self.bottom_pipe.update()
        self.top_pipe.update()

    def render(self, surface: pygame.Surface):
        """
        指定のサーフィスで自分を描画する

        Args:
            surface: 目標のサーフィス
        """
        self.bottom_pipe.render(surface)
        self.top_pipe.render(surface)

    def normalize_v(self):
        """垂直方向に動く速度を正規化して返す"""
        return self.v / MAX_PIPE_V if MAX_PIPE_V else 1


class Game:
    # 描画する画面
    screen: pygame.Surface = pygame.display.set_mode(
        (WIN_WIDTH, WIN_HEIGHT)
    )

    # 背景の画像オブジェクト
    bg_img: pygame.Surface = pygame.transform.scale(
        pygame.image.load(images['bg']).convert_alpha(),
        (WIN_WIDTH, WIN_HEIGHT - GND_HEIGHT)
    )

    # 早送りの倍数
    fast_forward: int = 1

    # 現在の点数
    score: int = 0
    # 最高点
    max_score: int = 0

    # 小鳥のリスト
    birds: List[Bird]
    # 土管対のリスト
    pipes: List[PipePair]
    # 地面のスプライト
    ground: Ground
    # 正方向に最も近い土管対
    frontier: PipePair

    # 小鳥の総数
    bird_count: int
    # 小鳥の残数
    remain_birds: int

    def __init__(self, bird_count=1):
        """
        ゲームを生成する

        Args:
            bird_count: 小鳥の総数
        """
        pygame.display.set_caption('Flappy Bird')
        self.bird_count = self.remain_birds = bird_count
        self.reset()

    def reset(self):
        """ゲームをリセットする"""
        self.score = 0
        self.pipes = [PipePair(WIN_WIDTH)]
        self.birds = [Bird() for _ in range(self.bird_count)]
        self.ground = Ground()
        self.frontier = self.pipes[0]

    def calc_remain(self):
        """残りの小鳥を数える"""
        count = 0
        for bird in self.birds:
            if bird.alive:
                count += 1
        self.remain_birds = count

    def flush_pipes(self):
        """土管を更新する"""
        if self.frontier.right <= self.birds[0].left:
            pipe = PipePair(WIN_WIDTH)
            self.pipes.append(pipe)
            self.frontier = pipe

        if self.pipes[0].right <= 0:
            self.pipes.pop(0)

    def update(self):
        """ゲームフレームを更新する"""
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
        """ゲームを描画する"""
        surface = self.screen
        surface.blit(self.bg_img, (0, 0))
        for pipe in self.pipes:
            pipe.render(surface)
        for bird in self.birds:
            if bird.alive:
                bird.render(surface)
        self.ground.render(surface)

    def draw_text(self, text: str, x: int, y: int):
        """
        指定の位置で文字列を描画する

        Args:
            text: 描画する文字列
            x: X 座標
            y: Y 座標
        """
        img = font.render(text, True, (255, 255, 255))
        self.screen.blit(img, (x, y))

    def change_speed(self, delta: int):
        """
        早送りの速度を変える

        Args:
            delta: 早送りの速度に足す量
        """
        self.fast_forward = max(1, self.fast_forward + delta)

    def start(self):
        """ゲームを開始する"""
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
