n = int (input ("输入整数"))
summary = 5 ; useful = 0 ; useless = 0 
while n != 0 :
    summary += n
    useful += 1
    if summary < 0 :
        print ("库存不足")
        useless += 1
        useful -= 1
        summary -= n
        
    n = int (input ("输入整数"))
print ("最终库存",summary,"成功操作次数",useful,"拒绝次数",useless)