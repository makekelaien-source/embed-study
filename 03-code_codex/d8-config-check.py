def check_config(expected,actual):
    dictionary = {"missing":[] ,"changed":[] ,"extra":[] }
    for item in expected:
        if item not in actual :
            dictionary["missing"].append(item)
        elif item in actual and expected[item] != actual[item]:
            dictionary["changed"].append(item)
    for item in actual :
        if item not in expected :
            dictionary["extra"].append(item)
    return dictionary



expected = {"east": 30, "west": 28, "north": 32}
actual = {"east": 30, "west": 35, "roof": 25}
dicktionary = check_config(expected,actual)
for item in dicktionary :
    print(dicktionary[item])