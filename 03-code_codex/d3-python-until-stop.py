temp = int (input ("整数温度"))
cold = 0 ; normal = 0 ; hot = 0
while temp != -999 :
    if temp >= 30 :
        hot +=1
        print ("高温")
    elif temp < 0 :
        cold += 1
        print ("低温")

    else :
        normal += 1
        print ("正常")
        
    temp = int (input ("整数温度"))
print ("高温总次数",hot)