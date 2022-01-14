import datetime

# We based our chaos generator on Chaos Monkey framework by Netflix - https://github.com/Netflix/chaosmonkey
# We are using their distrbutions and probability to introduce chaos into our system in the following forms:

# https://github.com/alexei-led/pumba

# 1) Reduce service capacity in a certain cluster.
#    This is the equivalent of terminating pods.
#    (Besides the fact the terminating pods also affect connected users) 
#    Probabilities: 
#    - The number of work days between terminations for an instance group is a random variable that has a geometric distribution
#    - Schedule a termination at a random time between 9AM and 3PM that day
# 2) Disconnect cluster
# 3) Introduce latency between clusters (within the hard coded avg)

# Configuration
meu = 5 # Mean time between termination in an experiment
epsilon = 0.5 # Min time between termination in an experiment

def random_chaos_into(clusters):
    for cluster in clusters:
        # TODO - adapt latency between zones?
        # TODO - drop service if needed - geometric prob
        # TODO - Disconnect cluster as a whole
        for key, service in cluster.services.items():
            break


def load_by_time_of_day_from(max_load, at_tik, gmt_offset_in_min):
    # tik equals 1 minute
    # tik 0 = 7AM GMT
    # at_tik = at_tik
    max_load = max_load * 1.1
    norm_tik = at_tik % 1_439
    norm_gmt_tik = (at_tik + gmt_offset_in_min) % 1_439
    local_tik = norm_gmt_tik / 60

    # print("local = {}\nmax_load = {}\nat_tik = {}\nnorm_tik = {}\nnorm_gmt_tik = {}\ngmt_offset_in_min = {}\n\n\n".format(local_tik, max_load, at_tik, norm_tik, norm_gmt_tik, gmt_offset_in_min))

    if local_tik >= 0 and local_tik < 1: # 00:00 - 00:59
      return max_load * (10/13)
    if local_tik >= 1 and local_tik < 2: # 01:00 - 01:59
      return max_load * (7/13)
    if local_tik >= 2 and local_tik < 3: # 02:00 - 02:59
      return max_load * (6/13)
    if local_tik >= 3 and local_tik < 4: # 03:00 - 03:59
      return max_load * (4/13)
    if local_tik >= 4 and local_tik < 5: # 04:00 - 04:59
      return max_load * (3/13)
    if local_tik >= 5 and local_tik < 6: # 05:00 - 05:59
      return max_load * (2.5/13)
    if local_tik >= 6 and local_tik < 7: # 06:00 - 06:59
      return max_load * (3/13)
    if local_tik >= 7 and local_tik < 8: # 07:00 - 07:59
      return max_load * (4/13)
    if local_tik >= 8 and local_tik < 9: # 08:00 - 08:59
      return max_load * (5/13)
    if local_tik >= 9 and local_tik < 10: # 09:00 - 09:59
      return max_load * (6/13)
    if local_tik >= 10 and local_tik < 11: # 10:00 - 10:59
      return max_load * (7.7/13)
    if local_tik >= 11 and local_tik < 12: # 11:00 - 11:59
      return max_load * (9/13)
    if local_tik >= 12 and local_tik < 13: # 12:00 - 12:59
      return max_load * (9/13)
    if local_tik >= 13 and local_tik < 14: # 13:00 - 13:59
      return max_load * (9.5/13)
    if local_tik >= 14 and local_tik < 15: # 14:00 - 14:59
      return max_load * (10/13)
    if local_tik >= 15 and local_tik < 16: # 15:00 - 15:59
      return max_load * (10/13)
    if local_tik >= 16 and local_tik < 17: # 16:00 - 16:59
      return max_load * (10.5/13)
    if local_tik >= 17 and local_tik < 18: # 17:00 - 17:59
      return max_load * (10.5/13)
    if local_tik >= 18 and local_tik < 19: # 18:00 - 18:59
      return max_load * (11.5/13)
    if local_tik >= 19 and local_tik < 20: # 19:00 - 19:59
      return max_load * (11/13)
    if local_tik >= 20 and local_tik < 21: # 20:00 - 20:59
      return max_load * (12/13)
    if local_tik >= 21 and local_tik < 22: # 21:00 - 21:59
      return max_load * (12/13)
    if local_tik >= 22 and local_tik < 23: # 22:00 - 22:59
      return max_load # Rush hour! 
    if local_tik >= 23 and local_tik < 24: # 23:00 - 23:59
      return max_load * (12/13)
    raise Exception("at_tik {}\ngmt_offset_in_min {}\norm_tik {}\nnorm_gmt_tik {}\nlocal_tik {}".format(at_tik, gmt_offset_in_min, norm_tik, norm_gmt_tik, local_tik))