# Teacher-prepared reuse of D7 student functions; no top-level calls.

def high_locations(readings,threshold):
    sum = []
    for item in readings :
        if readings[item] >= threshold :
            sum.append(item)
    return sum

def new_alert(previous,current, threshold):
    group2 = high_locations(current,threshold)
    for item in previous :
        if item in group2 and previous[item] >= threshold :
            group2.remove(item)
    return group2
