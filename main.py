import numpy as np

from game import Game
from network import *

bird_count = 50
hidden_nn = 3
mutation_rate = 0.1


class GameAI(Game):
    generation: Generation
    remain_birds: int

    def __init__(self):
        super().__init__(bird_count)
        genomes = []

        for _ in range(bird_count):
            w1 = np.random.randn(2, hidden_nn)
            b1 = np.random.randn(1, hidden_nn)
            w2 = np.random.randn(hidden_nn, 1)
            b2 = np.random.randn(1, 1)
            nn = NeuralNetwork(w1, b1, w2, b2)
            genomes.append(Genome(nn))

        self.generation = Generation(genomes)

    def calc_remain(self):
        count = 0
        for bird in self.birds:
            if bird.alive:
                count += 1
        self.remain_birds = count

    def update(self):
        super().update()

        self.calc_remain()

        if self.remain_birds == 0:
            self.reset()
            self.generation = self.generation.next(mutation_rate)
            return

        for i, genome in enumerate(self.generation.genomes):
            bird = self.birds[i]

            if not bird.alive:
                continue

            genome.fitness = bird.score

            offset = bird.get_offset(self.frontier)
            out = genome.nn.forward(np.array(offset))
            if out[0][0] > 0:
                bird.flap()

    def render(self):
        super().render()
        self.draw_text(f'Speed: {self.fast_forward}x', 10, 10)
        self.draw_text(f'Score: {self.score}', 10, 30)
        self.draw_text(f'Max Score: {self.max_score}', 10, 50)
        self.draw_text(f'Generation: {self.generation.id}', 10, 70)
        self.draw_text(f'Alive: {self.remain_birds}/{bird_count}', 10, 90)


if __name__ == '__main__':
    AI = GameAI()
    AI.start()
