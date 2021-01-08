#%%
import cvxpy as cp
import numpy as np

#%%
# game 1 is between team 1 and 2 in week ?
# game 2 is between team 1 and 3 in week ?
# ...
# game 11 is between team 2 and 3 in week ?
# ...
# game 18 is between team 2 and 10 in week ?
# game 19 is between team 3 and 4 in week ?
#
# ...
# game 45 is between team 9 and 10 in week ?

#%%
games = [[1, 2], [3, 4], [5, 6]]
games


#%%
# https://github.com/tonyelhabr/isye-6669/blob/master/hw-5/hw-5-responses.ipynb
def _solve_prob(obj, constrs):
    prob = cp.Problem(obj, constrs)
    prob.solve()
    print(f'status: {prob.status}')
    print(f'optimal value: {prob.value: .1f}')


def solve_prob(obj, constrs):
    return _solve_prob(obj, constrs)


#%%
# x1 = cp.Variable(1, integer=True)
# x2 = cp.Variable(1, integer=True)
# x3 = cp.Variable(1, integer=True)
# x4 = cp.Variable(1, integer=True)
# x5 = cp.Variable(1, integer=True)
# x6 = cp.Variable(1, integer=True)
x1 = cp.Variable(1)
x2 = cp.Variable(1)
x3 = cp.Variable(1)
x4 = cp.Variable(1)
x5 = cp.Variable(1)
x6 = cp.Variable(1)
x7 = cp.Variable(1)
x8 = cp.Variable(1)
x9 = cp.Variable(1)
x10 = cp.Variable(1)
x11 = cp.Variable(1)
x12 = cp.Variable(1)

constrs = [
    x1 == x4,
    x2 == x7,
    x3 == x10,
    x5 == x8,
    x6 == x11,
    x9 == x12,
    (x1 + x2 + x3) == 6,  # team 1's weeks should add up to 1 + 2
    (x4 + x5 + x6) == 6,  # team 2's weeks
    (x7 + x8 + x9) == 6,
    (x10 + x11 + x12) == 6,
    x1 <= x2,
    x2 <= x3,
    # x4 <= x5,
    x1 <= 3,
    x2 <= 3,
    x3 <= 3,
    x4 <= 3,
    x5 <= 3,
    x6 <= 3,
    x7 <= 3,
    x8 <= 3,
    x9 <= 3,
    x10 <= 3,
    x11 <= 3,
    x12 <= 3,
    x1 >= 1,
    x2 >= 1,
    x3 >= 1,
    x4 >= 1,
    x5 >= 1,
    x6 >= 1,
    x7 >= 1,
    x8 >= 1,
    x9 >= 1,
    x10 >= 1,
    x11 >= 1,
    x12 >= 1
]

obj = cp.Maximize(x1 + x2 + x3 + x4 + x5 + x6 + x7 + x8 + x9 + x10 + x11 + x12)
# obj = cp.Minimize(1)
solve_prob(obj, constrs)
print(f'x1: {x1.value}')
print(f'x2: {x2.value}')
print(f'x3: {x3.value}')
print(f'x4: {x4.value}')
print(f'x5: {x5.value}')
print(f'x6: {x6.value}')
print(f'x7: {x7.value}')
print(f'x8: {x8.value}')
print(f'x9: {x9.value}')
print(f'x10: {x10.value}')
print(f'x11: {x11.value}')
print(f'x12: {x12.value}')
#%%