'''
Created on May 13, 2014

@author: xiaoxubeii
'''
def __init__(self):
    print 'I am init'

def main():
    attrs = {"__init__":__init__}
    Hello = type("Hello", (object,), attrs)
    h = Hello()
    print type(h)
    
if __name__ == '__main__':
    main()
