def split(line:str, sep:str=None)->list:
    try:
        if sep is None:
            answer = line.split()
        else:
            answer = line.split(sep)
    except:
        answer = []
    return answer