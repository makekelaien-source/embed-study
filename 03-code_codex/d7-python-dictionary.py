sample = {"temperature": 26 ,"limit": 30}
sample["temperature"] = 33
print (sample ["temperature"])
if sample["temperature"] >= sample["limit"] :
    print ("ALARM")
else :
    print ("NORMAL")