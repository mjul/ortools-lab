"""
Scheduling nurses

See https://developers.google.com/optimization/scheduling/employee_scheduling

"""

from ortools.sat.python import cp_model


def nurse_scheduling_with_requests():
    num_nurses = 5
    num_shifts = 3
    num_days = 7
    all_nurses = range(num_nurses)
    all_shifts = range(num_shifts)
    all_days = range(num_days)

    # In addition to the variables from the previous example, the data also contains a set of triples, corresponding
    # to the three shifts per day. Each element of the triple is 0 or 1, indicating whether a shift was requested.
    # For example, the triple [0, 0, 1] in the fifth position of row 1 indicates that nurse 1 requests shift 3 on day
    # 5.
    shift_requests = [[[0, 0, 1], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 1],
                       [0, 1, 0], [0, 0, 1]],
                      [[0, 0, 0], [0, 0, 0], [0, 1, 0], [0, 1, 0], [1, 0, 0],
                       [0, 0, 0], [0, 0, 1]],
                      [[0, 1, 0], [0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 0, 0],
                       [0, 1, 0], [0, 0, 0]],
                      [[0, 0, 1], [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0],
                       [1, 0, 0], [0, 0, 0]],
                      [[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 0], [1, 0, 0],
                       [0, 1, 0], [0, 0, 0]]]

    model = cp_model.CpModel()

    shifts = {}
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                shifts[(n, d, s)] = model.NewBoolVar('shift_n%dd%is%i' % (n, d, s))

    # min_shifts_per_nurse is the largest integer such that every nurse
    # can be assigned at least that many shifts. If the number of nurses doesn't
    # divide the total number of shifts over the schedule period,
    # some nurses have to work one more shift, for a total of
    # min_shifts_per_nurse + 1.
    min_shifts_per_nurse = (num_shifts * num_days) // num_nurses
    max_shifts_per_nurse = min_shifts_per_nurse + 1
    for n in all_nurses:
        num_shifts_worked = sum(
            shifts[(n, d, s)] for d in all_days for s in all_shifts)
        model.Add(min_shifts_per_nurse <= num_shifts_worked)
        model.Add(num_shifts_worked <= max_shifts_per_nurse)

    model.Maximize(sum(shift_requests[n][d][s] * shifts[(n, d, s)]
                       for n in all_nurses
                       for d in all_days
                       for s in all_shifts))

    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0
    solver.Solve(model)

    for d in all_days:
        print('Day', d)
        for n in all_nurses:
            for s in all_shifts:
                if solver.Value(shifts[(n, d, s)]) == 1:
                    print('Nurse %i works shift %i (requested)' % (n, s))
                else:
                    print('Nurse %i works shift %i (not requested)' % (n, s))
        print()

    print()
    print('Statistics')
    print('  - Number of shift requests met = %i' % solver.ObjectiveValue(),
          '(out of', num_nurses * min_shifts_per_nurse, ')')
    print('  - wall time       : %f s' % solver.WallTime())


def main():
    nurse_scheduling_with_requests()


if __name__ == '__main__':
    main()
