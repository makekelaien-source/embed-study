num = 0 
n = int (input ("输入整轮轮数"))

for index in range (n) :
    temp = int (input ("请输入温度："))
    if temp < 0 :
        print ("低温")
    elif temp >= 30 :
        print("高温")
        num += 1
    else :
        print ("正常")
print ("高温总次数",num)