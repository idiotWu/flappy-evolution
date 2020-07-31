import numpy as np
from functools import reduce

from game import Game
from network import *

bird_count = 50
hidden_nn = 3
nn_input_dim = 3
nn_output_dim = 1

mutation_rate = 0.1


class GameAI(Game):
    generation: Generation
    # fast_forward = 404

    def __init__(self):
        super().__init__(bird_count)
        genomes = []

        for _ in range(bird_count):
            w1 = np.random.randn(nn_input_dim, hidden_nn)
            b1 = np.random.randn(hidden_nn)
            w2 = np.random.randn(hidden_nn, nn_output_dim)
            b2 = np.random.randn(nn_output_dim)
            nn = NeuralNetwork(w1, b1, w2, b2)
            genomes.append(Genome(nn))

        self.generation = Generation(genomes)

    def print_log(self):
        avg_score = reduce(
            lambda f1, f2: f1 + f2,
            (g.fitness for g in self.generation.genomes)
        ) / bird_count
        print(f'Gen: {self.generation.id}, Avg: {avg_score}, Max: {self.score}')

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
            x, y = bird.get_offset(self.frontier)
            out = genome.nn.forward(
                np.array([self.frontier.move_v, x, y])
            )
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
