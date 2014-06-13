'''
Created on Jun 4, 2014

@author: xiaoxubeii
'''

# DUMMY = 1
# 
# class Entry():
#     def __init__(self, key, value, index=None):
#         self.key = key
#         self.value = value
#         self.index = index
# 
# class Hash():
#     def __init__(self):
#         self._table = [Entry(None, None, i) for i in range(10)]
#         self.mask = 9
#         self.freeslot = None
#     
#     def _lookEntry(self, key, h):
#         e = self._table[h]
#         
#         # unused active dummy
#         # unused
#         if e.key is None and e.value is None:
#             if self.freeslot is None:
#                 return h
#             else:
#                 freelot = self.freelot
#                 return freelot
#         # active
#         else:
#             self.freeslot = None
#             
#             if e.key is not None and e.key != DUMMY and e.value is not None:
#                 pass
#             elif e.key == DUMMY and e.value is None:
#                 self.freeslot = h
#             
#             return self._lookEntry(key, h + 1)
#     
#     def hash(self, key):
#         return self.mask & key
#     
#     def add(self, entry):
#         h = self.hash(entry.key)
#         index = self._lookEntry(entry.key, h)
#         entry.index = index
#         self._table[index] = entry
#         
#         self.freeslot = None
#         
#     def __str__(self):
#         s = '{'
#         for e in self._table:
#             tmp = '"%s":"%s"' % (e.key, e.value) + ','
#             s = s + tmp
#         s = s[:len(s) - 1]
#         s = s + '}'
#             
#         return s
#         
# h = Hash()
# h.add(Entry(key=1, value=3))
# h.add(Entry(key=11, value=3))
# print h
class T():
        def __init__(self, name):
            self.name = name
            
        def __hash__(self):
            return hash(self.name)
            
        def __eq__(self, r):
            return self.name == r.name
    
dict = {}
t1 = T(name='t1')
dict[t1] = 1
t2 = T(name='t2')
dict[t2] = 2
t2.name = 't1'

print dict[t2]

        
        
        
