from random import normalvariate
import numpy as np
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

def heavy_tail_jobs_distribution(type = "pareto", jobs_count = 100, min_load = 45):
    if type == "pareto":
        return _pareto_job_disribution(jobs_count, min_load)


def _pareto_job_disribution(jobs_count, min_load):
    m = min_load
    a = 10
    size = (jobs_count,)
    s = (np.random.pareto(a, size = size) + 1) * m
    return s
