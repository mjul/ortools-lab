"""
Scheduling nurses

See https://developers.google.com/optimization/scheduling/employee_scheduling

"""

from __future__ import division
from __future__ import print_function
from ortools.sat.python import cp_model

num_nurses = 4
num_shifts = 3
num_days = 3

max_shifts_per_nurse_per_day = 1




class NursesPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shifts, num_nurses, num_days, num_shifts, sols):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shifts = shifts
        self._num_nurses = num_nurses
        self._num_days = num_days
        self._num_shifts = num_shifts
        self._solutions = set(sols)
        self._solution_count = 0

    def on_solution_callback(self):
        self._solution_count += 1
        if self._solution_count in self._solutions:
            print('Solution %i' % self._solution_count)
            for d in range(self._num_days):
                print('Day %i' % d)
                for n in range(self._num_nurses):
                    is_working = False
                    for s in range(self._num_shifts):
                        if self.Value(self._shifts[(n, d, s)]):
                            is_working = True
                            print('  Nurse %i works shift %i' % (n, s))
                    if not is_working:
                        print('  Nurse {} does not work'.format(n))
            print()

    def solution_count(self):
        return self._solution_count

all_nurses = range(num_nurses)
all_shifts = range(num_shifts)
all_days = range(num_days)

model = cp_model.CpModel()

shifts = {}

for n in all_nurses:
    for d in all_days:
        for s in all_shifts:
            shifts[(n, d, s)] = model.NewBoolVar('shift_n%dd%is%i' % (n, d, s))

# Max shifts per day
for n in all_nurses:
    for d in all_days:
        model.Add(sum(shifts[(n, d, s)] for s in all_shifts) <= max_shifts_per_nurse_per_day)


solver = cp_model.CpSolver()
solver.parameters.linearization_level = 0

a_few_solutions = range(5)
solution_printer = NursesPartialSolutionPrinter(shifts, num_nurses, num_days, num_shifts, a_few_solutions)

solver.SearchForAllSolutions(model, solution_printer)

# Statistics

print()
print('Statistics')
print('  - conflicts       : %i' % solver.NumConflicts())
print('  - branches        : %i' % solver.NumBranches())
print('  - wall time       : %f s' % solver.WallTime())
print('  - solutions found : %i' % solution_printer.solution_count())

