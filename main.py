import numpy as np
from functools import reduce

from game import Game
from network import NeuralNetwork, Genome, Generation

bird_count = 50

nn_input_dim = 3
nn_hidden_dim = 3
nn_output_dim = 1

mutation_rate = 0.1


class GameAI(Game):
    generation: Generation
    fast_forward = 102400

    def __init__(self):
        super().__init__(bird_count)
        genomes = []

        for _ in range(bird_count):
            w1 = np.random.randn(nn_input_dim, nn_hidden_dim)
            b1 = np.random.randn(nn_hidden_dim)
            w2 = np.random.randn(nn_hidden_dim, nn_output_dim)
            b2 = np.random.randn(nn_output_dim)
            nn = NeuralNetwork(w1, b1, w2, b2)
            genomes.append(Genome(nn))

        self.generation = Generation(genomes)

    def print_log(self):
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
        super().update()

        if self.remain_birds == 0:
            self.print_log()
            self.generation = self.generation.next(mutation_rate)
            self.reset()
            return

        for i, genome in enumerate(self.generation.genomes):
            bird = self.birds[i]

            if not bird.alive:
                continue

            genome.fitness = bird.score
            x, y = bird.normalize_offset(self.frontier)
            pipe_v = self.frontier.normalize_v()
            out = genome.nn.forward(np.array([x, y, pipe_v]))
            if out[0] >= 0:
                bird.flap()

    def render(self):
        super().render()
        self.draw_text(f'SPEED: {self.fast_forward}x', 10, 10)
        self.draw_text(f'SCORE: {self.score}', 10, 35)
        self.draw_text(f'HIGH SCORE: {self.max_score}', 10, 60)
        self.draw_text(f'GENERATION: {self.generation.id}', 10, 85)
        self.draw_text(f'ALIVE: {self.remain_birds} / {bird_count}', 10, 110)


if __name__ == '__main__':
    AI = GameAI()
    AI.start()
