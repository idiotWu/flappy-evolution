from __future__ import annotations

import random
import numpy as np
from dataclasses import dataclass
from typing import List


@dataclass
class NeuralNetwork:
    # 入力層から隠れ層への重み
    w1: np.ndarray
    # 入力層から隠れ層へのバイアス
    b1: np.ndarray
    # 隠れ層から出力層への重み
    w2: np.ndarray
    # 隠れ層から出力層へのバイアス
    b2: np.ndarray

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        ニューラルネットワークから出力を得る

        Args:
            x: 入力

        Returns: 出力
        """
        z1 = np.tanh(x.dot(self.w1) + self.b1)
        z2 = np.tanh(z1.dot(self.w2) + self.b2)
        return z2


@dataclass
class Genome:
    # この個体に対応するニューラルネットワーク
    nn: NeuralNetwork
    # 個体の適応度
    fitness: float = 0

    @staticmethod
    def crossover(a: np.ndarray, b: np.ndarray):
        """
        2 つのパラメータを交差する

        Args:
            a: パラメータ a
            b: パラメータ b

        Returns: 交差後のパラメータ
        """
        # return 0.5 * (a + b)
        mask = np.random.uniform(size=a.shape)
        return np.where(mask <= 0.5, a, b)

    @staticmethod
    def mutate(a: np.ndarray, mutation_rate: float):
        """
        パラメータに変異を行う

        Args:
            a: パラメータ
            mutation_rate: 変異率

        Returns: 変異後のパラメータ
        """
        mask = np.random.uniform(size=a.shape)
        multiplier = np.where(
            mask <= mutation_rate,
            np.random.uniform(0, 2, size=a.shape),
            np.ones(a.shape)
        )

        return a * multiplier

    def breed(self, g2: Genome, mutation_rate: float) -> Genome:
        """
        もう 1 つの親個体と子個体を世代する

        Args:
            g2: 目標の親個体
            mutation_rate: 子個体の変異率

        Returns: 子個体
        """
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
    # この世代の ID
    id: int = 0
    # この世代の個体リスト
    genomes: List[Genome]

    def __init__(self, genomes: List[Genome]):
        """
        世代を生成する

        Args:
            genomes: この世代の個体リスト
        """
        Generation.id += 1
        self.genomes = genomes

    def next(self, mutation_rate):
        """
        次の世代を生成する

        Args:
            mutation_rate: 子個体の変異率

        Returns: 次の世代
        """
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
