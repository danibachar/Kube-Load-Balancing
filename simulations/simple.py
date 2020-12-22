import time, random, math, json, threading
import numpy as np
from scipy.optimize import linprog
from scipy.stats import pareto, lognorm
from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable

from matplotlib import pyplot as plt

import itertools

import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
# def 〈source,arrival−time,load,duration,destinations,type〉

count = 0

# Round Robin
def test(a,b,c):
    global count
    print("begin\na={}\nb={}\nc={}\ncount={}\n".format(a,b,c,count))
    count += 1
    time.sleep(random.randint(0,5))
    count -= 1
    print("end\na={}\nb={}\nc={}\ncount={}\n".format(a,b,c,count))


def run():
    letters = [1,2,3,4,5,6,7,78,8,9,9,9,6,3,3]
    threads = []
    for i in range(0,10):
        a = random.choice(letters)
        b = random.choice(letters)
        c = random.choice(letters)
        thread = threading.Thread(target = test, args=(a,b,c))
        threads.append(thread)
        thread.start()

    for t in threads:
        t.join()

# run()

async def consume():
    await asyncio.sleep(1)
    return random.choice([True, False])

async def test_1():
    did_succeed = await consume()
    print("did_succeed = ", did_succeed)

# Python 3.7+
# asyncio.run(test_1())

def blocking_io():
    # File operations (such as logging) can block the
    # event loop: run them in a thread pool.
    with open('/dev/urandom', 'rb') as f:
        return f.read(100)

def cpu_bound():
    # CPU-bound operations will block the event loop:
    # in general it is preferable to run them in a
    # process pool.
    return sum(i * i for i in range(10 ** 7))



async def proccess_and_thread():
    loop = asyncio.get_running_loop()

    ## Options:

    # 1. Run in the default loop's executor:
    result = await loop.run_in_executor(
        None, blocking_io)
    print('default thread pool', result)

    # 2. Run in a custom thread pool:
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool, blocking_io)
        print('custom thread pool', result)

    # 3. Run in a custom process pool:
    with concurrent.futures.ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool, cpu_bound)
        print('custom process pool', result)

# asyncio.run(proccess_and_thread())

# Initialize 10 threads
THREAD_POOL = ThreadPoolExecutor(3)

def synchronous_handler(sleep_time, message):
    # Do something synchronous
    print("before - ", message)
    time.sleep(sleep_time)
    print("after - ", message)
    return "foo"

# Somewhere else
async def main():
    loop = asyncio.get_event_loop()
    it = [(0.5, "0.5"),(0.25, "0.25"),(1, "1"),(3, "3")]
    futures = []
    for i in it:
        futures.append(loop.run_in_executor(THREAD_POOL, synchronous_handler, i[0], i[1]))

    # futures = [
    #     loop.run_in_executor(THREAD_POOL, synchronous_handler, 0.5, "0.5"),
    #     loop.run_in_executor(THREAD_POOL, synchronous_handler, 0.25, "0.25"),
    #     loop.run_in_executor(THREAD_POOL, synchronous_handler, 1, "1"),
    #     loop.run_in_executor(THREAD_POOL, synchronous_handler, 3, "3"),
    # ]
    await asyncio.wait(futures)
    for future in futures:
        print(future.result())
#
# with THREAD_POOL:
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())


# from load_balancing.round_robin import round_robin, smooth_weighted_round_robin
#
# options = [1,2,3,4,5]
# weights = [1,0.01,0.01,0.01,0.01]
# key = "key"
#
# for i in range(0,10):
#     print(smooth_weighted_round_robin(options, weights, key))

def _pareto_job_disribution():
    lower = 50  # the lower bound for your values - minimal job count
    shape = 2   # the distribution shape parameter, also known as `a` or `alpha`
    size = 20 # the size of your sample (number of random values)
    # jobs_distribution = (np.random.pareto(a=shape, size=(0,5,size)) + 1) * lower
    # jobs_distribution = np.random.pareto(a=shape, size=size) + lower
    # jobs_distribution = np.random.pareto(a=50, size=size)
    # x = np.linspace(0, 30, 100)
    # jobs_distribution = pareto.pdf(x, scale = 1, b = 50)
    x = np.linspace(0, 50, 1000)
    jobs_distribution = pareto.pdf(x, 50, 20, 30)
    return jobs_distribution

# x = np.linspace(0, 70, 20)
# print(x)
# jobs_distribution = pareto.pdf(x, scale = 40, b = 1)
# print(jobs_distribution)
# plt.plot(x, jobs_distribution)
# plt.show()

# m = 5
# size = (200,)
# a = 10#size[0]*m
# s = (np.random.pareto(a, size = size) + 1) * m
# # s = np.random.pareto(a, size = size)
# print(s)
# count, bins, _ = plt.hist(s, 100, density=True)
# plt.show()

# mu = 0.
# sigma = 0.5
# s = np.random.lognormal(mu, sigma, 1000)
# print(s)
# count, bins, ignored = plt.hist(s, 100, density=True, align='mid')
# plt.show()


def lognorm_params(mode, stddev):
    """
    Given the mode and std. dev. of the log-normal distribution, this function
    returns the shape and scale parameters for scipy's parameterization of the
    distribution.
    """
    p = np.poly1d([1, -1, 0, 0, -(stddev/mode)**2])
    r = p.roots
    sol = r[(r.imag == 0) & (r.real > 0)].real
    shape = np.sqrt(np.log(sol))
    scale = mode * sol
    return shape, scale

# mode = 123
# stddev = 99
# sigma, scale = lognorm_params(mode, stddev)
# sample = lognorm.rvs(sigma, 0, scale, size=1000)
# print(sample)
# tmp = plt.hist(sample, normed=True, bins=1000, alpha=0.6, color='c', ec='c')
# plt.show()


obj = [-1, -2]
#      ─┬  ─┬
#       │   └┤ Coefficient for y
#       └────┤ Coefficient for x

lhs_ineq = [[ 2,  1],  # Red constraint left side
             [-4,  5],  # Blue constraint left side
             [ 1, -2]]  # Yellow constraint left side

rhs_ineq = [20,  # Red constraint right side
             10,  # Blue constraint right side
              2]  # Yellow constraint right side

lhs_eq = [[-1, 5]]  # Green constraint left side
rhs_eq = [15]       # Green constraint right side

bnd = [(0, float("inf")),  # Bounds of cluster 1
        (0, float("inf")),  # Bounds of cluster 2
        ]

opt = linprog(c=obj, A_ub=lhs_ineq, b_ub=rhs_ineq,
                A_eq=lhs_eq, b_eq=rhs_eq, bounds=bnd,
                method="revised simplex")

# print(opt)

job_type = "product_page"
dest_job = "review"
job_load = 1

# job_type -> dest_job
jobs = [1,1,1,1,1,1,1]
clusters = [
    {
        "cost": 100,
        "residual_capacity": 1
    },
    {
        "cost": 30,
        "residual_capacity": 2
    },
    {
        "cost": 100,
        "residual_capacity": 3
    },
]


obj = []

lhs_ineq = []
rhs_ineq = []

# for j_idx, job in enumerate(jobs):
#     # obj.append([])
#     prefix = len(clusters) * j_idx
#     for s_idx, cluster in enumerate(clusters):
#         obj.append(cluster["cost"]) # objective to minimize the cost
#
#         # rhs_ineq.append([])
#         rhs_ineq.append(cluster["residual_capacity"])
#
#         lhs_ineq.append([])
#         for d_idx, dest_cluster in enumerate(clusters):
#             if s_idx == d_idx:
#                 lhs_ineq[prefix+s_idx].append(job)
#             else:
#                 lhs_ineq[prefix+s_idx].append(0)
#         print("jobs round = ", j_idx)
#         print("cluster round = ", s_idx)
#         print("c = ", obj)
#         print("A_ub = ", lhs_ineq)
#         print("b_ub = ", rhs_ineq)

# for j_idx, job in enumerate(jobs):
#     obj.append([])
#     prefix = len(clusters) * j_idx
#     for s_idx, cluster in enumerate(clusters):
#         obj[j_idx].append(cluster["cost"]) # objective to minimize the cost
#
#         rhs_ineq.append([])
#         rhs_ineq[prefix+s_idx].append(cluster["residual_capacity"])
#
#         lhs_ineq.append([])
#         for d_idx, dest_cluster in enumerate(clusters):
#             if s_idx == d_idx:
#                 lhs_ineq[prefix+s_idx].append(job)
#             else:
#                 lhs_ineq[prefix+s_idx].append(0)
        # print("jobs round = ", j_idx)
        # print("cluster round = ", s_idx)
        # print("c = ", obj)
        # print("A_ub = ", lhs_ineq)
        # print("b_ub = ", rhs_ineq)

# rhs_ineq = [ cluster["residual_capacity"] for cluster in clusters for _ in range(int(len(lhs_ineq)/subset_size)) ]


# for c_idx, cluster in enumerate(clusters):
#     obj.append(cluster["cost"]) # objective to minimize the cost
#
#     prefix = len(jobs) * c_idx
#     for j_idx, job in enumerate(jobs):
#         lhs_ineq.append([])
#         for idx, _ in enumerate(clusters):
#             if idx == c_idx:
#                 lhs_ineq[prefix+j_idx].append(job)
#             else:
#                 lhs_ineq[prefix+j_idx].append(0)
#         # left side constraits - job load
#         # lhs_ineq[c_idx].append(jobs_list)
#         # Right side constrai residual capacity (what is left)
#         rhs_ineq.append(cluster["residual_capacity"])

# Additional constriat - that all prs must sum to 1
lhs_eq = [[1,1,1]]
rhs_eq = [1]

bnd = [(0, 1), (0, 1), (0, 1)]

# opt = linprog(
#     c=obj,
#     A_ub=lhs_ineq,
#     b_ub=rhs_ineq,
#     A_eq=lhs_eq,
#     b_eq=rhs_eq,
#     bounds=bnd,
#     method='interior-point',
#     options = { "presolve": False }#, 'cholesky': False, "sym_pos": False}
# )
# print("c = ", obj)
# print("A_ub = ", lhs_ineq)
# print("b_ub = ", rhs_ineq)
# print("A_eq = ", lhs_eq)
# print("b_eq = ", rhs_eq)
# print(opt)
jobs_count = len(jobs)
jobs_sum = sum(jobs)
subset_size = len(clusters)
perms = [i for i in range(jobs_sum+1) for _ in range(subset_size)]

options = list(set(filter(lambda x: sum(x) == jobs_sum, itertools.permutations(perms, subset_size))))
assert len(options)/subset_size - int(len(options)/subset_size) == 0

obj = [cluster["cost"] for cluster in clusters]
rhs_ineq = [cluster["residual_capacity"] for cluster in clusters]

# (index, cost, max_strech_ratio)
def sum_opt(op, max_cost, max_streching_ratio):
    return op["cost"]/max_cost * 0.5 + op["max_strech_ratio"]/max_streching_ratio * 0.5

best_opt = {
    "opt_index": -1,
    "cost": float('inf'),
    "max_strech_ratio": float('inf'),
}

# max cost will be to send all jobs to the most expensive clusters
max_cost = max([cluster["cost"] for cluster in clusters])*jobs_sum
# max ratio will be to send all jobs to the least available cluster
max_ratio = jobs_count/min([cluster["residual_capacity"] for cluster in clusters])

print("max_cost = ",max_cost)
print("max_ratio = ",max_ratio)

for opt_idx, opt in enumerate(options):
    tmp_opt = {
        "opt_index":opt_idx,
        "cost": 0,
        "max_strech_ratio": -1,
    }
    assert len(opt) == len(clusters)
    for c_idx, cluster in enumerate(clusters):
        jobs_to_send = opt[c_idx]
        tmp_opt["cost"]+=jobs_to_send*cluster["cost"]
        tmp_opt["max_strech_ratio"] = max(tmp_opt["max_strech_ratio"], jobs_to_send/cluster["residual_capacity"])

    if sum_opt(tmp_opt, max_cost, max_ratio) < sum_opt(best_opt, max_cost, max_ratio):
        print("hit")
        best_opt = tmp_opt

print("best_opt = ", best_opt)
print("best_opt opt = ", options[best_opt["opt_index"]])

opts = []

# for option in options:
#     lhs_ineq = []
#
#     for o_idx, op in enumerate(option):
#         tmp = []
#         for idx, o in enumerate(option):
#             if idx == o_idx:
#                 tmp.append(o)
#             else:
#                 tmp.append(0)
#         lhs_ineq.append(tmp)
#
#     print("c = ", obj)
#     print("A_ub = ", lhs_ineq)
#     print("b_ub = ", rhs_ineq)
#     print("A_eq = ", lhs_eq)
#     print("b_eq = ", rhs_eq)
#
#     opt = linprog(
#         c=obj,
#         A_ub=lhs_ineq,
#         b_ub=rhs_ineq,
#         A_eq=lhs_eq,
#         b_eq=rhs_eq,
#         bounds=bnd,
#         method='interior-point',
#         options = { "presolve": False }#, 'cholesky': False, "sym_pos": False}
#     )
#     opts.append((opt, option))
#
# success_opts = list(filter(lambda o: o[0].success,opts))
# print(success_opts)
# jobs_sum = sum(jobs)
# subset_size = len(clusters)
# perms = [i for i in range(jobs_sum+1) for _ in range(subset_size)]
#
# # print(list(itertools.permutations(perms,3)))
# combos = set(filter(lambda x: sum(x) == jobs_sum, itertools.permutations(perms, subset_size)))
# print(combos)
# print(len(combos))
