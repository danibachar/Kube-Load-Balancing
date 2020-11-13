from random import normalvariate

# Chossing element from list, according to normal distribution
def normal_choice(lst, mean=None, stddev=None):
    if len(lst) == 0:
        return None
        
    if mean is None:
        # if mean is not specified, use center of list
        mean = (len(lst) - 1) / 2

    if stddev is None:
        # if stddev is not specified, let list be -3 .. +3 standard deviations
        stddev = len(lst) / 6

    while True:
        index = int(normalvariate(mean, stddev) + 0.5)
        if 0 <= index < len(lst):
            return lst[index]
