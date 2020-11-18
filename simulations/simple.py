import time, random, math, json, threading
import numpy as np
from scipy.optimize import linprog

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


from load_balancing.round_robin import round_robin, smooth_weighted_round_robin

options = [1,2,3,4,5]
weights = [1,0.01,0.01,0.01,0.01]
key = "key"

for i in range(0,10):
    print(smooth_weighted_round_robin(options, weights, key))
