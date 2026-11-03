# Teacher-prepared dependency: student function from d7-python-filter.py.
def keep_at_least(values, threshold):
    selected = []
    for item in values :
        if item >= threshold :
            selected.append(item)
    return selected


original = [2, 5, 9]
kept = keep_at_least(original, 5)
kept.append(7)

print(original)
print(kept)
