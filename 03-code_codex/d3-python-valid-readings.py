temp = int (input ("整数温度"))
useful = 0; summary = 0 ; hot = 0 ; useless = 0
while temp != -999 :
    if temp == -888:
        print("无效读数")
        useless += 1
    else :
        useful += 1
        summary += temp
        if temp >= 30 :
            hot += 1
    temp = int (input ("整数温度"))
print ("有效次数",useful,"无效次数",useless,"有效总和", summary,"高温次数",hot)