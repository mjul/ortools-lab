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

    num_drivers = 6
    num_timeblocks = 6
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

    # Create the indicator variables for a driver having a free day (not working)
    free_days = {}
    for driver in all_drivers:
        for day in all_days:
            free_days[(driver, day)] = model.NewBoolVar('free_day_driver%i_day%i' % (driver, day))

    # A day is free if there are no not-free blocks for the driver
    for driver in all_drivers:
        for day in all_days:
            free_day = free_days[(driver, day)]
            for block in all_timeblocks:
                free_block = timeblocks[(driver, day, block, State.FREE.value)]
                # if any block is not free, the day is not free
                model.AddImplication(free_block.Not(), free_day.Not())
                # if the day is free, all the blocks must be free
                model.AddImplication(free_day, free_block)

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
            is_working_day = free_days[(driver, day)].Not()
            model.Add(sum(timeblocks[(driver, day, block, state.value)]
                          for block in all_timeblocks
                          for state in all_work_states)
                      >= (min_total_timeblocks_per_driver_per_working_day * is_working_day))

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

    status = solver.Solve(model)

    print("Solver status: ", solver.StatusName(status))

    if status != cp_model.INFEASIBLE:

        for day in all_days:
            print('-- Day %i' % day)
            for driver in all_drivers:
                is_free_day = solver.BooleanValue(free_days[(driver, day)])
                print('Driver %i is free? %s' % (driver, is_free_day))
                for block in all_timeblocks:
                    for state in State:
                        if solver.Value(timeblocks[(driver, day, block, state.value)]):
                            print('Driver %i block %i doing %s' % (driver, block, state.name))

    # Statistics.
    print()
    print('Statistics')
    print(solver.ResponseStats())


if __name__ == '__main__':
    driver_scheduling()
