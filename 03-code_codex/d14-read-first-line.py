def read_first_line(path) :
    try :
        with open(path,"r",encoding="utf-8") as stream :
            line = stream.readline()
        return line
    except FileNotFoundError :
        return None