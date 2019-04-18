"""
Driver scheduling

Example with added work/break policies.

Based on https://developers.google.com/optimization/scheduling/employee_scheduling
"""

from __future__ import division
from __future__ import print_function
from ortools.sat.python import cp_model

from enum import IntEnum, unique


@unique
class State(IntEnum):
    FREE = 0
    DRIVE = 1
    REST = 2

    def is_work(self):
        return self.value != State.FREE


class DriversPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, timeblocks, num_drivers, num_days, num_timeblocks, sols):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._timeblocks = timeblocks
        self._num_drivers = num_drivers
        self._num_days = num_days
        self._num_timeblocks = num_timeblocks
        self._solutions = set(sols)
        self._solution_count = 0

    def on_solution_callback(self):
        self._solution_count += 1
        if self._solution_count in self._solutions:
            print('Solution %i' % self._solution_count)
            for day in range(self._num_days):
                print('Day %i' % day)
                for driver in range(self._num_drivers):
                    is_working = False
                    for block in range(self._num_timeblocks):
                        for state in State:
                            if self.Value(self._timeblocks[(driver, day, block, state.value)]):
                                if state.is_work():
                                    is_working = True
                                print('  Driver %i works time-block %i (%s)' % (driver, block, state.name))
                    if not is_working:
                        print('  Driver {} does not work'.format(driver))
            print()

    def solution_count(self):
        return self._solution_count


def driver_scheduling():
    minutes_per_timeblock = 30

    num_drivers = 3
    num_timeblocks = 8
    num_days = 1

    # Min and max working time (including breaks)
    min_total_timeblocks_per_driver_per_working_day = 4
    max_total_timeblocks_per_driver_per_day = 5

    # Max consecutive driving blocks without rest
    max_consecutive_driving_timeblocks = 2

    all_drivers = range(num_drivers)
    all_timeblocks = range(num_timeblocks)
    all_days = range(num_days)
    all_states = [s for s in State]
    all_work_states = [s for s in all_states if s.is_work()]

    # Creates the model.
    model = cp_model.CpModel()

    # Creates time-block variables.
    # timeblocks[(dr, day, bl, st)]: driver 'dr' works block 'bl' on day 'day' doing state 'st'
    timeblocks = {}
    for driver in all_drivers:
        for day in all_days:
            for block in all_timeblocks:
                for state in all_states:
                    timeblocks[(driver, day, block, state)] = model.NewBoolVar(
                        'timeblock_driver%i_day%i_block%i_state%i' % (driver, day, block, state))

    # Each time block has exactly one driver driving
    for day in all_days:
        for block in all_timeblocks:
            model.Add(sum(timeblocks[(driver, day, block, State.DRIVE.value)] for driver in all_drivers) == 1)

    # Each driver can do only one thing in each time-block
    for driver in all_drivers:
        for day in all_days:
            for block in all_timeblocks:
                model.Add(sum(timeblocks[(driver, day, block, state.value)] for state in State) == 1)

    # Max time-blocks per day including rest
    for driver in all_drivers:
        for day in all_days:
            model.Add(sum(timeblocks[(driver, day, block, state.value)]
                          for block in all_timeblocks
                          for state in all_work_states)
                      <= max_total_timeblocks_per_driver_per_day)

    # Min time-blocks per working day including rest
    for driver in all_drivers:
        for day in all_days:
            model.Add(sum(timeblocks[(driver, day, block, state.value)]
                          for block in all_timeblocks
                          for state in all_work_states)
                      >= min_total_timeblocks_per_driver_per_working_day)

    # Max consecutive time-blocks without rest
    for driver in all_drivers:
        for day in all_days:
            for start_block_index in range(num_timeblocks):
                too_much_driving = all_timeblocks[
                                   start_block_index:start_block_index + max_consecutive_driving_timeblocks + 1:]
                if len(too_much_driving) == max_consecutive_driving_timeblocks + 1:
                    model.Add(sum(timeblocks[(driver, day, block, State.DRIVE.value)]
                                  for block in too_much_driving)
                              <= max_consecutive_driving_timeblocks)

    # Create the solver and solve
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0
    solver.parameters.max_time_in_seconds = 10.0
    # Display the first few solutions.
    a_few_solutions = range(2)
    solution_printer = DriversPartialSolutionPrinter(
        timeblocks, num_drivers, num_days, num_timeblocks, a_few_solutions)
    solver.SearchForAllSolutions(model, solution_printer)

    # solver.Solve(model)

    # Statistics.
    print()
    print('Statistics')
    print('  - conflicts       : %i' % solver.NumConflicts())
    print('  - branches        : %i' % solver.NumBranches())
    print('  - wall time       : %f s' % solver.WallTime())
    print('  - solutions found : %i' % solution_printer.solution_count())


if __name__ == '__main__':
    driver_scheduling()
