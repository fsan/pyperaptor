def concat(x, *args):
    return list(x) + list(args)

def printer(x):
    print(x)
    return x

def printer_N(*x):
    print(x)
    return x

def printer_2(*x):
    print(x[1])
    return x

def returner(x):
    return x

def pair_first(*a):
        return a[0]

def pair_second(*a):
        return a[1] 

def retrieve_1(_, b):
    return b

def retrieve_N(_, *b):
    return b

def make_pair(a,b):
    return (a,b)

def make_tuple(a,*b):
    return (a,b)