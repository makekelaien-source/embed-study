# Teacher preparation only; not a student solution.
def add_one(value):
    return value + 1

assert add_one(4) == 5
values = [4, -2, 7]
assert len(values) == 3 and values[1] == -2
assert list(iter(values)) == [4, -2, 7]
first = [1, 2]
second = first
second[0] = 9
assert first == [9, 2]
second = [7]
assert first == [9, 2]
assert len([]) == 0
print("PYTHON_DEMOS_PASS")
