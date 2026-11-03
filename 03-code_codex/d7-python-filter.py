def keep_at_least(values, threshold):
    selected = []
    for item in values :
        if item >= threshold :
            selected.append(item)
    return selected

values = [2,5,5,9]
values = keep_at_least(values,5)
print (values)