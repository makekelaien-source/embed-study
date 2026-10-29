summary = 0 ; cnt = 0
while True :
    num = int (input ("整数"))
    if num == 0 :
        break
    else :
        summary += num
        cnt += 1
print ("总和",summary, "次数", cnt)