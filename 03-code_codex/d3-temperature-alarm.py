n =  int (input ("轮数"))

con = 0
con_max = 0 ; positon = -1 ; cnt = 0 


for index in range (n) :
    num = int (input ("整数温度"))
    if num >= 30 :
        con += 1
        cnt += 1
        if con == 3 and positon == -1 :
            positon = index
        if con_max < con :
            con_max = con
    else :
        con = 0
if n== 0 :
    print("无温度输入")
print ("高温总次数",cnt)
print ("最长连续高温数",con_max)
print ("报警下标",positon)