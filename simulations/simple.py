import time, random, math, json, threading
import numpy as np
from scipy.optimize import linprog


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

import asyncio

async def consume():
    await asyncio.sleep(1)
    return random.choice([True, False])

async def test_1():
    did_succeed = await consume()
    print("did_succeed = ", did_succeed)

# Python 3.7+
asyncio.run(test_1())
