# Teacher copy of your D8 check_config from the 2026-11-04 study book.
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
