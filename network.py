from __future__ import annotations

import random
import numpy as np
from dataclasses import dataclass
from typing import List


@dataclass
class NeuralNetwork:
    w1: np.ndarray
    b1: np.ndarray
    w2: np.ndarray
    b2: np.ndarray

    def forward(self, x: np.ndarray) -> np.ndarray:
        z1 = np.tanh(x.dot(self.w1) + self.b1)
        z2 = np.tanh(z1.dot(self.w2) + self.b2)
        return z2


@dataclass
class Genome:
    nn: NeuralNetwork
    fitness: float = 0

    @staticmethod
    def crossover(a: np.ndarray, b: np.ndarray):
        # return 0.5 * (a + b)
        mask = np.random.uniform(size=a.shape)
        return np.where(mask <= 0.5, a, b)

    @staticmethod
    def mutate(a: np.ndarray, mutation_rate: float):
        mask = np.random.uniform(size=a.shape)
        multiplier = np.where(
            mask <= mutation_rate,
            np.random.uniform(0, 2, size=a.shape),
            np.ones(a.shape)
        )

        return a * multiplier

    def breed(self, g2: Genome, mutation_rate: float) -> Genome:
        maps = (
            (self.nn.w1, g2.nn.w1),
            (self.nn.b1, g2.nn.b1),
            (self.nn.w2, g2.nn.w2),
            (self.nn.b2, g2.nn.b2),
        )

        params = []

        for a, b in maps:
            p = self.crossover(a, b)
            params.append(self.mutate(p, mutation_rate))

        nn = NeuralNetwork(*params)

        return Genome(nn)


class Generation:
    id: int = 0
    genomes: List[Genome]

    def __init__(self, genomes: List[Genome]):
        Generation.id += 1
        self.genomes = genomes

    def next(self, mutation_rate):
        self.genomes.sort(key=lambda gen: gen.fitness, reverse=True)
        # best_genome = self.genomes[0]
        total_count = len(self.genomes)
        max_children = 10

        # new_genomes = [
        #     g.breed(g, 0) for g in self.genomes[:10]
        # ]
        new_genomes = []

        for g in self.genomes:
            for _ in range(max_children):
                g2 = self.genomes[random.randrange(total_count)]
                new_genomes.append(g.breed(g2, mutation_rate))
                if len(new_genomes) == total_count:
                    return Generation(new_genomes)

            if max_children > 1:
                max_children -= 1
