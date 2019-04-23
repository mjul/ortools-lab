"""Add implication relations to Boolean variables"""
from __future__ import division
from __future__ import print_function
from ortools.sat.python import cp_model

from enum import IntEnum, unique


class ImplicationsPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, variables, sols):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._variables = variables
        self._solutions = set(sols)
        self._solution_count = 0

    def on_solution_callback(self):
        self._solution_count += 1
        if self._solution_count in self._solutions:
            print('Solution %i' % self._solution_count)
            for k in sorted(self._variables.keys()):
                v = self._variables[k]
                vval = self.BooleanValue(v)
                print('  %s -> %i' % (v, vval))
            print()

    def solution_count(self):
        return self._solution_count


def implications():
    model = cp_model.CpModel()
    variables = {}
    a = variables['a'] = model.NewBoolVar('a')
    b = variables['b'] = model.NewBoolVar('b')
    c = variables['c'] = model.NewBoolVar('c')

    model.AddImplication(a, c)
    model.AddImplication(a.Not(), c.Not())
    model.AddImplication(b, c)

    solver = cp_model.CpSolver()
    solutions_to_print = range(8)
    solution_printer = ImplicationsPartialSolutionPrinter(variables, solutions_to_print)

    solver.SearchForAllSolutions(model, solution_printer)

    # Statistics.
    print()
    print('Statistics')
    print('  - conflicts       : %i' % solver.NumConflicts())
    print('  - branches        : %i' % solver.NumBranches())
    print('  - wall time       : %f s' % solver.WallTime())
    print('  - solutions       : %i' % solution_printer.solution_count())


if __name__ == '__main__':
    implications()
