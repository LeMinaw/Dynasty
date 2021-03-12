"""This module simulates trajectories of interacting particles in 3D space.\n
Particles are called "Walkers", in reference to the fact at each iteration each
particle is "walking" towards or away from others. Various mathematical
interaction laws and relationship generation rules are provided, yielding very
different simulation results.
"""

from collections import namedtuple
from dataclasses import dataclass
from operator import attrgetter
from time import perf_counter_ns
import numpy as np
from numpy.random import default_rng

from dynasty.utils import LabeledEnum


def rand_spread_array(shape, avg=0, var=1, rng=None):
    """Generate a ndarray with given shape populated with random float
    values in the range ]avg-var, avg+var[.
    """
    rng = rng or default_rng()
    return var * (2*rng.random(shape) - 1) + avg


def diff_array(array):
    """Returns a square matrix of all differences of an array's elements.

    Example: diffs([a; b; c]) ->
    a-a b-a c-a
    a-b b-b c-b
    a-c b-c c-c
    """
    tile = np.tile(array, np.size(array, axis=0))
    return tile - tile.T


class InterLaw(LabeledEnum):
    """Enumeration of interaction laws.\n
    Impacts the mathematical formula binding walkers together.
    """
    POSITION = 0, "Distance fraction"
    VELOCITY = 1, "Velocity"
    NEWTON_LINEAR = 2, "Newton's (linear)"
    NEWTON = 3, "Newton's (quadratic)"
    # CYCLICAL = 4, "Cyclical"


class RelModel(LabeledEnum):
    """Enumeration of relation models.\n
    Impacts relation mask generation.
    """
    ONE_TO_ONE   = 0, "One to one"
    SPARSE       = 1, "Sparse (25%)"
    MANY_TO_MANY = 2, "Many to many"


class SeedableRNG:
    """Class that wraps a NumPy pseudo-random `Generator`, and provide utility
    methods to restart or reseed it.
    """
    def __init__(self, seed=None):
        self.seed = seed
        self.generator = default_rng(seed)

    def reseed(self, seed=None):
        """Reseed the PRNG.\n
        If no `seed` argument is given, the last seed will be used, hence the
        PRNG will generate the same sequence of numbers again.
        """
        if seed is not None:
            self.seed = seed
        self.generator = default_rng(self.seed)


@dataclass
class SystemParameters:
    count: int = 3
    spread: float = 10
    inter_law: InterLaw = InterLaw.POSITION
    rel_model: RelModel = RelModel.ONE_TO_ONE
    rel_avg: float = .1
    rel_var: float = 0
    iterations: int = 10


SystemRNGs = namedtuple('RNGs', ('start_pos', 'rel_mask', 'rel_matrix'))


class WalkerSystem:
    def __init__(self, params=SystemParameters()):
        self.params = params

        # Use perf_counter_ns for seeding, because time_ns precision is very
        # poor on some systems - Windows, not to name it
        self.rngs = SystemRNGs(
            *(SeedableRNG(perf_counter_ns() + i) for i in range(3))
        )

        # Those will be populated later by various computing methods
        self.rel_mask, self.rel_matrix = None, None
        self.start_pos, self.positions = None, None

    def generate_start_pos(self):
        rng = self.rngs.start_pos
        rng.reseed()

        # Start pos in ]-1, 1[
        self.start_pos = rand_spread_array(
            (self.params.count, 3), rng=rng.generator
        )

    def generate_relation_mask(self):
        n, model = attrgetter('count', 'rel_model')(self.params)

        rng = self.rngs.rel_mask
        rng.reseed()

        if model == RelModel.ONE_TO_ONE:
            # One walker is in relation with another
            self.rel_mask = np.roll(np.eye(n, dtype=bool), 1, axis=1)

        elif model == RelModel.SPARSE:
            # SPARSE is MANY_TO_MANY with only 25% of relations
            # As the diagonal will be nulled hereafter, a small density
            # compensation is needed to maintain a final 25% probability
            self.rel_mask = rng.generator.random((n, n)) < (.25 + 1/n)

        else:
            # Each walker is in relation with all others
            self.rel_mask = np.ones((n, n), dtype=bool)

        # Fill diagonal to False, because a walker can't interact with itself
        np.fill_diagonal(self.rel_mask, False)

    def generate_relation_matrix(self):
        n, avg, var = attrgetter('count', 'rel_avg', 'rel_var')(self.params)

        rng = self.rngs.rel_matrix
        rng.reseed()

        self.rel_matrix = rand_spread_array(
            (n, n), avg, var, rng=rng.generator
        )
        self.rel_matrix *= self.rel_mask

        # TODO: Replacement to the removed ELECTRONIC interaction model:
        # It might be interesting to have a global switch to make any relation
        # matrix reciprocal (eg. by taking its upper triangle submatrix,
        # transposing it, then overwriting the lower triangle)

    def compute_pos(self):
        law = self.params.inter_law
        rels = self.rel_matrix

        pos = self.start_pos * self.params.spread
        vel = np.zeros_like(pos)

        positions = []
        for _ in range(self.params.iterations):
            positions.append(pos.copy())

            if law == InterLaw.POSITION:
                # A specific part of the distance between a walker and the
                # others will be added to its position.
                pos += rels @ pos - np.einsum('ij,iz->iz', rels, pos)
                # pos += rels @ pos - np.sum(rels @ pos, axis=0)
                # pos += (rels @ pos) - np.sum(rels * pos, axis=0)


            elif law == InterLaw.CYCLICAL:
                # Alg that does not uses attraction directly but variances
                # between attraction values as position modulation.
                pos += rels @ pos - (pos.T @ rels).T

            else:
                forces = diff_array(pos) # Distance between all walkers locations
                # TODO: Port an test those laws
                # if law in (InterLaw.NEWTON_LINEAR, InterLaw.NEWTON):
                #     # Newton's and Coulomb's forces norms are of form k/d².
                #     # newtonlinear is variation of form k/d
                #     # normalize(f) returns a direction vector of norm 1, while
                #     # norm.(f).^pow is the norm of the new force vector.
                #     exp = -2 if law == InterLaw.NEWTON else -1
                #     forces = 10**4 * normalize(forces) * norm(forces) ** exp
                #     np.fill_diagonal(forces, 0)

                # Forces are modulated by walkers relations, then instant velocity
                # is incremented by the resulting acceleration. Position is then
                # incremented by instant velocity.
                vel += np.sum(.1 * rels * forces, axis=1)
                pos += vel

        self.positions = np.array(positions)


if __name__ == '__main__':
    sys = WalkerSystem()
    sys.generate_start_pos()
    print(sys.start_pos)
    sys.generate_relation_mask()
    print(sys.rel_mask)
    sys.generate_relation_matrix()
    print(sys.rel_matrix)
    sys.compute_pos()
    print(sys.positions)
    print(sys.positions.shape)
