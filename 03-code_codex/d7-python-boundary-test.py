# Correct version: prepared from the student's existing function.
def count_at_(values, threshold):
    a = 0
    for value in values:
        if value >= threshold:
            a += 1
    return a


# Teacher-injected bug: > replaces >=.
def count_wrong(values, threshold):
    a = 0
    for value in values:
        if value > threshold:
            a += 1
    return a


# Runnable starter case; change these three lines to expose the bug.
values = [2, 9]
threshold = 5
expected = 1

print("expected:", expected)
print("correct:", count_at_(values, threshold))
print("wrong:", count_wrong(values, threshold))
