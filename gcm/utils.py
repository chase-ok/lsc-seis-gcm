
from bisect import bisect_left
import collections
import functools
import os

class memoized(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__

    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)


def float_find_index(sorted_array, x, epsilon=1e-10):
    i = bisect_left(sorted_array, x)
    if i != len(sorted_array) and abs(sorted_array[i] - x) < epsilon:
        return i
    elif i != 0 and abs(sorted_array[i - 1] - x) < epsilon:
        return i - 1
    else:
        raise ValueError("{0} not found.".format(x))

def get_directories(root):
    for name in os.listdir(root):
        if os.path.isdir(os.path.join(root, name)):
            yield name

def get_files(root):
    for name in os.listdir(root):
        if os.path.isfile(os.path.join(root, name)):
            yield name
