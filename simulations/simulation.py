import time, random, math, json, threading, logging

from datetime import datetime
from numpy import random

from models.kubernetes import Job
from generators.application_generator import generate_application
from load_balancing.round_robin import round_robin

now = datetime.now()
log_file_name = 'simulation.{}.log'.format(now)
logging.basicConfig(filename=log_file_name, level=logging.INFO)



clusters, front_end = generate_application(round_robin)

def job_count():
    lower = 5  # the lower bound for your values - minimal job count
    shape = 2   # the distribution shape parameter, also known as `a` or `alpha`
    size = 50 # the size of your sample (number of random values)
    jobs_distribution = random.pareto(a=shape, size=size) + lower

single_job = Job(None, 0.25, 1, front_end)
def load(cluster, time):

    for t in range(0,time):
        continue

for cluster in clusters:
    # thread = threading.Thread(target = load, args = (cluster,30))
    thread = threading.Thread(target = cluster.consume, args = (single_job,))
    thread.start()

# time.sleep(5)
traffic_map = {}
for cluster in clusters:
    cluster.wait_for_jobs_to_finish()
    traffic = cluster.sum_traffic_sent()
    traffic_map[cluster.id] = traffic

print("traffic_map = ",traffic_map)
