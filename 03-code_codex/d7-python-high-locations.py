def high_locations(readings,threshold):
    sum = []
    for item in readings :
        if readings[item] >= threshold :
            sum.append(item)
    return sum    

vocabulary = {"north":26, "south": 33, "roof": 30}
print (high_locations(vocabulary,30))
