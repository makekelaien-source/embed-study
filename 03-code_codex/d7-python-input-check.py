# Teacher-prepared dependency: student function from d7-python-list-function.py.
def count_at_(values,threshold):
    a = 0
    for value in values :
        if value >= threshold :
            a += 1
    return  a


# Student: write only the new input-preservation test below.
values = [2,5,5,9]
before = values.copy()
b = count_at_(values,5)
print (b)
if values == before :
    print ("True")
else :
    print ("False")