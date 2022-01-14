
import logging, threading, collections

class State:
    round_robin_map = {}
    weighted_round_robin_map = {}

    lock = threading.Lock()

state = State()

def reset_state():
    state.lock.acquire()
    state.round_robin_map = {}
    state.weighted_round_robin_map = {}
    state.lock.release()

# Classic Round Robin disregard the weights
def round_robin(options, weights, key):
    state.lock.acquire()
    if key not in state.round_robin_map:
        state.round_robin_map[key] = 0
    rr_counter = state.round_robin_map[key]
    logging.info("destination round robin function for:{}\ncounter:{}".format(key, rr_counter))
    selection = options[rr_counter%len(options)]
    state.round_robin_map[key] = rr_counter + 1
    state.lock.release()
    return selection

# Smooth Weighted Round Robin
def smooth_weighted_round_robin(options, weights, key):
    if len(options) != len(weights):
        raise Exception("smooth_weighted_round_robin 1")
    if len(options) == 0:
        raise Exception("smooth_weighted_round_robin 2")
    if len(options) == 1:
        return options[0]

    state.lock.acquire()
    if key not in state.weighted_round_robin_map:
        state.weighted_round_robin_map[key] = collections.OrderedDict()

    weight_sum = sum(weights)
    num_of_options = len(options)

    for idx in range(0,num_of_options):
        weight = weights[idx]
        option = options[idx]

        if option not in state.weighted_round_robin_map[key]:
            state.weighted_round_robin_map[key][option] = ItemWeight(option, weight)

    total_weight = 0
    result = None

    selection_map = state.weighted_round_robin_map[key]
    for option, item in selection_map.items():
        # print("option:{}\nitem:{}".format(option, item))
        item.current_weight += item.effective_weight
        total_weight += item.effective_weight
        if item.effective_weight < item.weight:
            item.effective_weight += 1
        if not result or result.current_weight < item.current_weight:
            result = item

    result.current_weight -= total_weight

    if result == None:
        raise

    state.lock.release()
    return result.item

# Copied - https://github.com/linnik/roundrobin/blob/master/roundrobin/smooth_rr.py
class ItemWeight:

    def __init__(self, item, weight):
        self.item = item
        self.weight = weight
        self.current_weight = 0
        self.effective_weight = weight

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
