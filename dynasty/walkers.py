import numpy as np
from numpy.random import default_rng
from enum import Enum
from dataclasses import dataclass
from operator import attrgetter
from time import perf_counter_ns


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


class InterLaw(Enum):
    POSITION = 0
    VELOCITY = 1
    NEWTON_LINEAR = 2
    NEWTON = 3
    CYCLICAL = 4


class RelModel(Enum):
    ONE_TO_ONE = 0
    SPARSE = 1
    MANY_TO_MANY = 2
    ELECTRONIC = 3


@dataclass
class SystemParameters:
    count: int = 3
    spread: float = 10
    inter_law: InterLaw = InterLaw.POSITION
    rel_model: RelModel = RelModel.ONE_TO_ONE
    rel_avg: float = .1
    rel_var: float = 0
    iterations: int = 10


class WalkerSystem:
    def __init__(self, params=SystemParameters()):
        self.params = params

        # Use perf_counter_ns for seeding, because time_ns precision is very
        # poor on some systems - Windows, not to name it
        self.start_pos_seed = perf_counter_ns()
        self.rel_mask_seed = perf_counter_ns() + 1
        self.rel_matrix_seed = perf_counter_ns() + 2

    def generate_start_pos(self):
        rng = default_rng(self.start_pos_seed)

        # Start pos in ]-1, 1[
        self.start_pos = rand_spread_array((self.params['count'], 3), rng=rng)

    def generate_relation_mask(self):
        n, model = attrgetter('count', 'rel_model')(self.params)

        rng = default_rng(self.rel_mask_seed)

        if model == RelModel.ONE_TO_ONE:
            # One walker is in relation with another
            self.rel_mask = np.roll(np.eye(n, dtype=bool), 1, axis=1)

        elif model == RelModel.SPARSE:
            # SPARSE is MANY_TO_MANY with only 25% of relations.
            # As the diagonal will be nulled, compensation is needed.
            self.rel_mask = rng.random((n, n)) < (.25 + 1/n)

        # TODO: Port this relation model
        # elif model == RelModel.ELECTRONIC:
        #     # Relation matrix as if each walker behaves as a +/- charged particule
        #     loads = repeat(rand(rng, n), 1, n)
        #     rel = -transpose(loads) .* loads

        else:
            # Each walker is in relation with all others
            self.rel_mask = np.ones((n, n), dtype=bool)

        # Fill diagonal to False, because a walker can't interact with itself
        np.fill_diagonal(self.rel_mask, False)

    def generate_relation_matrix(self):
        n, avg, var = attrgetter('count', 'rel_avg', 'rel_var')(self.params)

        rng = default_rng(self.rel_matrix_seed)

        self.rel_matrix = rand_spread_array((n, n), avg, var, rng=rng)
        self.rel_matrix *= self.rel_mask

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
