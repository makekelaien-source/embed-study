import d8_alert_tools

def new_positions(privious,current):
    a = d8_alert_tools.new_alert(privious,current,30)
    return a

previous = {"east":35,"west":18}
current = {"east":36,"west":30}
a = new_positions(previous,current)
print(a)