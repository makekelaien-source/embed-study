def count_at_(values,threshold):
    a = 0
    for value in values :
        if value >= threshold :
            a += 1
    return  a

answer = count_at_([2,5,5,9],5)
print (answer)