n = int(input("输入非负整数轮数n"))
num = 0
first = -1
for index in range (n) :
    temp = int (input ("请输入温度："))
    if temp < 0 :
        print ("低温")
    elif temp >= 30 :
        print("高温")
        num += 1
        if first ==-1 :
            first = index
    else :
        print ("正常")
print ("高温总次数",num)
print ("首次高温位置",first)