# Teacher-prepared dependency: student high_locations from d7-python-high-locations.py.
def high_locations(readings,threshold):
    sum = []
    for item in readings :
        if readings[item] >= threshold :
            sum.append(item)
    return sum

def new_alert(previous,current, threshold):
    group2 = high_locations(current,threshold)
    group1 = []
    for item in previous :
        for value in current :
            if value != item : 
                group1.append(value)
    for item in previous :
        if previous[item] < threshold & previous[item] not in group2 & previous[item] not in group1:
            group1.append(item)
    group1 += group2
    return group1





previous = {"north": 30, "south": 32}
current= {"north": 31, "south": 35, "roof": 30}
print (new_alert(previous,current,30))
# Student: implement new_alert_locations(previous, current, threshold) below.
# Reuse high_locations(current, threshold); do not rewrite the existing helper.
