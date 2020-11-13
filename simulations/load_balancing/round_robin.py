
import logging

round_robin_map = {}

def round_robin(options, key):
    if key not in round_robin_map:
        round_robin_map[key] = 0
    rr_counter = round_robin_map[key]
    logging.info("destination round robin function for:{}\ncounter:{}".format(key, rr_counter))
    selection = options[rr_counter%len(options)]
    round_robin_map[key] = rr_counter + 1
    return selection
