'''
Created on May 20, 2014

@author: xiaoxubeii
'''
# import kombu_rpc
# import nova_rpc
# result = nova_rpc.call('{"method":"echo","args":{"value":"hello"}}')
# # result = kombu_rpc.call('{"method": "echo", "args":{"value": "hello"}}')
# print result

# from itertools import *

# class Test():
#     def __call__(self):
#         print "success"
#     def __iter__(self):
#         while True:
#             pass
#         
# t = Test()
# list(t)
# mygenerator = (x*x for x in range(3))
# for i in mygenerator:
#     print  i
#     
# for i in mygenerator:
#     print i


# def fab(max):
#     n, a, b = 0, 0, 1
#     while n < max:
#         yield b
#         a, b = b, b + a
#         n = n + 1
#              
# while True:
#     pass

# import nova_rpc_test
# msg = nova_rpc_test.call('{"method":"echo","args":{"value":"hello"}}')
# print msg

def calculate(m):
    if m == 0:
        return 0
    return calculate(m - 1) + m

# print calculate(5)

def _find(index, array, number, value):
    
    if index == number:
        return -1
    
    if array[index] == value:
        return index
    
    return _find(index + 1, array, number, value)

def find(array, number, value):
    return _find(0, array, number, value)

# print find((1, 2, 3, 4), 4, 4)

def iterate(value):
    count = 0
    number = 0
    s = []
    
    s.append(value)
    
    while s:
        number = s.pop()
        if number != 1:
            s.append(number - 1)
        count += number
    
    return count

def binary_search(array, value):
    start = 0
    end = len(array) - 1
    
    
    while start <= end:
        middle = start + ((end - start) >> 1)
        if array[middle] == value:
            return middle
        else:
            if array[middle] > value:
                end = middle - 1
            else:
                start = middle + 1
                
def insert_sort(param):
    for j in range(1, len(param)):
        i = j - 1
        key = param[j]
        while i >= 0 and param[i] > key:
            param[i + 1] = param[i]
            i = i - 1
            
        param[i + 1] = key
        
    return param
            
print insert_sort([3, 1, 2, 3, 10, 2, 4, 6, 7])
        



