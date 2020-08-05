import numpy as np
from functools import reduce

from game import Game
from network import NeuralNetwork, Genome, Generation

# 小鳥の数（＝ ニューラルネットワーク数）
bird_count = 50

# ニューラルネットワークで各層の次元数
nn_input_dim = 3
nn_hidden_dim = 3
nn_output_dim = 1

# 子個体の変異率
mutation_rate = 0.1


class GameAI(Game):
    # 世代情報
    generation: Generation
    # 早送りの倍数
    # fast_forward = 1024

    def __init__(self):
        super().__init__(bird_count)
        genomes = []

        # 最初世代のパラメータはランダム的に生成する
        for _ in range(bird_count):
            w1 = np.random.randn(nn_input_dim, nn_hidden_dim)
            b1 = np.random.randn(nn_hidden_dim)
            w2 = np.random.randn(nn_hidden_dim, nn_output_dim)
            b2 = np.random.randn(nn_output_dim)
            nn = NeuralNetwork(w1, b1, w2, b2)
            genomes.append(Genome(nn))

        self.generation = Generation(genomes)

    def print_log(self):
        """今世代における学習の結果を出力する"""
        fit = [g.fitness for g in self.generation.genomes]
        fit.sort()

        avg_score = reduce(lambda f1, f2: f1 + f2, fit) / bird_count

        print('Gen: {}, Mean: {:.2f}, Min: {}, Median: {}, Max: {}, 1e3+: {}, 1e4+: {}'.format(
            self.generation.id,
            avg_score,
            fit[0],
            fit[bird_count // 2],
            fit[-1],
            len([f for f in fit if f > 1e3]),
            len([f for f in fit if f > 1e4])
        ))

    def update(self):
        """ゲームフレームの更新"""
        super().update()

        # 生存者がなければ次の世代を生成する
        if self.remain_birds == 0:
            self.print_log()
            self.generation = self.generation.next(mutation_rate)
            self.reset()
            return

        for i, genome in enumerate(self.generation.genomes):
            bird = self.birds[i]

            if not bird.alive:
                continue

            # 個体の適応度を記録する
            genome.fitness = bird.score
            # ネットワークのパラメータ
            x, y = bird.normalize_offset(self.frontier)
            pipe_v = self.frontier.normalize_v()
            # ネットワークの出力
            out = genome.nn.forward(np.array([x, y, pipe_v]))
            # 出力が 0 以上ならば小鳥を飛ばす
            if out[0] >= 0:
                bird.flap()

    def render(self):
        """情報を描画する"""
        super().render()
        self.draw_text(f'SPEED: {self.fast_forward}x', 10, 10)
        self.draw_text(f'SCORE: {self.score}', 10, 35)
        self.draw_text(f'HIGH SCORE: {self.max_score}', 10, 60)
        self.draw_text(f'GENERATION: {self.generation.id}', 10, 85)
        self.draw_text(f'ALIVE: {self.remain_birds} / {bird_count}', 10, 110)


if __name__ == '__main__':
    AI = GameAI()
    AI.start()
