
from scipy.optimize import linprog
import numpy
import time, random, math, json
import networkx as nx
import matplotlib.pyplot as plt

import helpers

TOPOLOGY_KEY = "TOPOLOGY"
LOAD_KEY = "LOAD"
COST_KEY = "COST"
PRICE_KEY = "PRICE"
LATENCY_KEY = "LATENCY"

MAX_LOAD = 100

CLUSTERS_NAMES = ["C0","C1","C2"]
SERVICE_MAP = {
    0: "Product",
    1: "Reviews1",
    2: "Reviews2",
    3: "Reviews3",
    4: "Details",
    5: "Rating",
}

SERVICE_LOCATION_MAP = {

}

def mock_sample_application_dependecy_graph():
    G = nx.DiGraph()
    for i in range(6):
        G.add_node(i)
    # from product page to details and review
    for i in range(4):
        G.add_edge(0,i+1)
    # from reviews v2/3 to rating
    G.add_edge(1,5)
    G.add_edge(2,5)

    return G

def mock_topology_mapping(G): # Note - G must be DAG
    full_map = {}
    full_map.setdefault(TOPOLOGY_KEY, {})
    full_map.setdefault(LOAD_KEY, {})

    for node in G.nodes: # First add all services Dep Map and Load Map
        node_name = SERVICE_MAP[node]
        full_map[TOPOLOGY_KEY].setdefault(node_name, {"dep": [], "clusters": []})
        full_map[LOAD_KEY].setdefault(node_name, {})
        for c in CLUSTERS_NAMES:
          # If service is not part of any cluster yet - add to random cluster
          if len(full_map[TOPOLOGY_KEY][node_name]["clusters"]) == 0:
            rand_first_cluster = random.choice(CLUSTERS_NAMES)
            full_map[TOPOLOGY_KEY][node_name]["clusters"].append(rand_first_cluster)
          # else add with prob 0.5 to another cluster
          elif random.randint(0,1) == 0:
            clusters_service_not_in = list(set(CLUSTERS_NAMES) - set(full_map[TOPOLOGY_KEY][node_name]["clusters"]))
            if len(clusters_service_not_in) > 0:
              full_map[TOPOLOGY_KEY][node_name]["clusters"].append(random.choice(clusters_service_not_in))

    for edge in G.edges: # Second build dependency JSON
        src_node = SERVICE_MAP[edge[0]]
        dst_node = SERVICE_MAP[edge[1]]
        if dst_node not in full_map[TOPOLOGY_KEY][src_node]["dep"]:
          full_map[TOPOLOGY_KEY][src_node]["dep"].append(dst_node)

    return full_map

def mock_random_cost(full_map):
    full_map.setdefault(COST_KEY, {})
    full_map[COST_KEY].setdefault(PRICE_KEY, {})
    full_map[COST_KEY].setdefault(LATENCY_KEY, {})
    for ci in CLUSTERS_NAMES:
        full_map[COST_KEY][PRICE_KEY].setdefault(ci, {})
        full_map[COST_KEY][LATENCY_KEY].setdefault(ci, {})
        for cv in CLUSTERS_NAMES:
            if cv == ci: # Setting zero cost for in-cluster communication
                full_map[COST_KEY][PRICE_KEY][ci][cv] = 0
                full_map[COST_KEY][LATENCY_KEY][ci][cv] = 0
                continue
            full_map[COST_KEY][PRICE_KEY][ci][cv] = random.random()
            full_map[COST_KEY][LATENCY_KEY][ci][cv] = random.randint(20,2000)

def mock_rand_load(full_map):
    for s in full_map[TOPOLOGY_KEY].keys(): # For each Source Service
        for dep_s in full_map[TOPOLOGY_KEY][s]["dep"]: # For each Target Service
            for s_ci in full_map[TOPOLOGY_KEY][s]["clusters"]: # For each Source Service Location
                for dep_s_cv in full_map[TOPOLOGY_KEY][dep_s]["clusters"]: # For each Target Service Locaiton
                    key = helpers.construct_service_to_service_key(s, s_ci, dep_s, dep_s_cv)
                    if key in full_map[LOAD_KEY][dep_s]:
                        full_map[LOAD_KEY][dep_s][key] = math.floor(random.random() * MAX_LOAD)
                    else:
                        full_map[LOAD_KEY][dep_s].setdefault(key, math.floor(random.random() * MAX_LOAD))

def _get_max_cost(cluster_cost_map):
    max_cost = -1
    for sc, cost_map in cluster_cost_map.items():
        for tc, cost in cost_map.items():
            max_cost = max(cost, max_cost)
    return max_cost

def _get_max_latency(cluster_latency_map):
    max_cost = -1
    for sc, cost_map in cluster_latency_map.items():
        for tc, cost in cost_map.items():
            max_cost = max(cost, max_cost)
    return max_cost


def extract_max_latency_max_price(full_map):
    max_price = -1
    max_latency = -1
    for cost_type, cost_map in full_map[COST_KEY].items():
        if cost_type == PRICE_KEY:
            max_price = _get_max_cost(cost_map)
        if cost_type == LATENCY_KEY:
            max_latency = _get_max_cost(cost_map)
    return max_price, max_latency

def calculate_pareto_cost(latency, price, max_price, max_latency):
    return price/max_price + latency/max_latency

def sum_rr_cost(full_map):
    total_system_cost = 0
    cluster_to_cluster_cost = full_map[COST_KEY]
    service_to_service_load = full_map[LOAD_KEY]

    max_price, max_latency = extract_max_latency_max_price(full_map)

    for scv_name, svc_incoming_load in service_to_service_load.items():
        for svc_to_svc_name, load  in svc_incoming_load.items():
            s, sc, t, tc = helpers.reconstruct_service_cluster_from_key(svc_to_svc_name)
            price = cluster_to_cluster_cost[PRICE_KEY][sc][tc]
            latency = cluster_to_cluster_cost[LATENCY_KEY][sc][tc]
            total_system_cost += calculate_pareto_cost(latency, price, max_price, max_latency)

    return total_system_cost

def sum_rr_load(full_map):
    total_system_load = 0

    service_to_service_load = full_map[LOAD_KEY]
    for scv_name, svc_incoming_load in service_to_service_load.items():
        for svc_to_svc_name, load  in svc_incoming_load.items():
            total_system_load+=load

    return total_system_load

def rr_static_cost_rand_load_over_time(time, full_map):
    costs = []
    loads = []
    times = []
    for t in range(time):
        print("Before")
        print(full_map[LOAD_KEY])
        mock_rand_load(full_map)
        print("After")
        print(full_map[LOAD_KEY])
        costs.append(sum_rr_cost(full_map))
        loads.append(sum_rr_load(full_map))
        times.append(t)
    return costs, loads, times


def location_aware_application_graph_from_topology(t):
  G = nx.DiGraph()
  nodes = {}
  for srv_name in t[TOPOLOGY_KEY].keys():
    srv = t[TOPOLOGY_KEY][srv_name]
    for cluster in srv["clusters"]:
      node_name = "{}.{}".format(srv_name, cluster)
      node_idx = len(nodes)
      G.add_node(node_idx) # adding node
      nodes[node_name] = node_idx # keeping node name - mapping between name to node index on the graph
  edges = {}
  sinks_capacity = {}
  for s in t[TOPOLOGY_KEY].keys(): # For each Source Service
    for s_ci in t[TOPOLOGY_KEY][s]["clusters"]: # For each Source Service Location
      for dep_s in t[TOPOLOGY_KEY][s]["dep"]: # For each Target Service
        for dep_s_cv in t[TOPOLOGY_KEY][dep_s]["clusters"]: # For each Target Service Locaiton
          src_name = "{}.{}".format(s, s_ci)
          sink_name = "{}.{}".format(dep_s, dep_s_cv)
          src_idx = nodes[src_name]
          sink_idx = nodes[sink_name]
          # TODO - actual weights and capacities
          w = random.randint(1,12)
          c = sinks_capacity.get(sink_name,None)
          if c is None:
            c = random.randint(10,50)
            sinks_capacity[sink_name] = c

          edge_name = "{}-{}".format(src_name, sink_name)
          edges[edge_name] = {"w":w, "c":c}
          # edges[(src_idx, sink_idx))] = "w={}, c={}".foramt(w,c)
          G.add_edge(src_idx, sink_idx, weight=w, capacity=c)

  return G, nodes, edges

def transform(dic):
    transformed_dic = {}
    for key, value in dic.items():
        transformed_dic[value] = key
    return transformed_dic

def draw(G, labels, add_edges_labels=False):
    pos = nx.spring_layout(G, k=100)
    nx.draw_networkx(G, node_size=3500, labels=labels, pos=pos, with_labels=True, font_size=9)
    if add_edges_labels:
        nx.draw_networkx_edge_labels(G, pos=pos)
    plt.axis('off')
    plt.show()

# First generate the general applicaiton layout
G_a = mock_sample_application_dependecy_graph()
# Construct Cluster Dependent Topology
full_map = mock_topology_mapping(G_a)
# Generate radomize cost - Latency and Price for now
mock_random_cost(full_map)
# Simulates Load in Topology
mock_rand_load(full_map)
print(full_map)

# Draw Application Graph
print("Application dependencies Graph")
draw(G_a, SERVICE_MAP)

# Genrate Application Locatoin Aware Graph And Draw
print("Application Location Aware Graph")
G_al, nodes, edges = location_aware_application_graph_from_topology(full_map)
draw(G_al, transform(nodes))

# Sum Round Robin COST
print("Sum of cost in the system according to Round Robin - i.e random")
costs, loads, times = rr_static_cost_rand_load_over_time(20, full_map)

# print(costs)
# print(loads)
# print(times)

# costs = [1, 2, 3, 4]
# loads = [2, 7, 5, 40]
# times = [1, 2, 3, 4]

# plt.plot(times, costs, 'r--', times, loads, 'b--')
# plt.show()

fig, ax1 = plt.subplots()
ax1.set_xlabel('timem (min)')

color = 'tab:red'
ax1.set_ylabel('cost', color=color)
ax1.plot(times, costs, color=color)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

color = 'tab:blue'
ax2.set_ylabel('load', color=color)  # we already handled the x-label with ax1
ax2.plot(times, loads, color=color)
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.show()

# # Network Flow based optimization
# def _edge_name(src,sink):
#     return "{}-{}".format(src,sink)
#
# def smart_cap(supply_per_source, sources, sinks, sinks_caps):
#   total_supply = sum(supply_per_source)
#   total_cap = sum(sinks_caps)
#   total_weight = sum([ edges[_edge_name(s, si)]["w"] for s in sources for si in sinks ])
#   cap_map = {}
#   ratio_sum = 0
#   for si in range(len(sinks)):
#     # total_weight_on_sink = sum([ edges[_edge_name(s, sinks[si])]["w"] for s in sources ])
#     for s in range(len(sources)):
#       my_weight = edges[_edge_name(sources[s], sinks[si])]["w"]
#
#       my_weight_share = my_weight / total_weight
#       my_supply_share = supply_per_source[s] / total_supply
#       my_cap_share = sinks_caps[si] / total_cap
#
#       ratio = (my_supply_share + my_cap_share)/2
#       ratio_sum+=ratio
#
#       cap_map[_edge_name(sources[s], sinks[si])] = round(ratio*supply_per_source[s])
#   print("ratio sum = {}".format(ratio_sum))
#   return cap_map
#
#
#
#   for s in range(len(sorces)):
#     sup = supply_per_source[s]
#     w = 0
#     for si in range(len(sinks)):
#       w += weights[s+si]
#     for si in range(len(sinks)):
#       return 3
#
# def is_source_service_location_affect_target_service_location(source, sink, cluster):
#   is_dependent = sink in full_map[TOPOLOGY_KEY][source]["dep"]
#   in_current_cluster = cluster in full_map[TOPOLOGY_KEY][source]["clusters"]
#   return not is_dependent or not in_current_cluster
#
# def services_affecting(sink, cluster):
#   res = []
#   for source in full_map[TOPOLOGY_KEY].keys():
#     if is_source_service_location_affect_target_service_location(source, sink, cluster):
#       continue
#     res.append(source)
#   return res
#
# def depended_sources(sink):
#   res = [ ]
#   topology = full_map[TOPOLOGY_KEY]
#   for srv in topology.keys():
#     srv_meta = topology[srv]
#     if sink in srv_meta["dep"]:
#       for c in srv_meta["clusters"]:
#         res.append("{}.{}".format(srv,c))
#   return res
#
# def source_services_in_cluster(cluster):
#   topology = full_map[TOPOLOGY_KEY]
#   res = [ ]
#   for srv in topology.keys():
#     srv_meta = topology[srv]
#     if cluster not in srv_meta["clusters"]:
#       continue
#     if len(srv_meta["dep"]) > 0: # this is not a source service as it is not depened on any other
#       res.append(srv)
#   return res
#
#
# def target_services_affected_by_cluster(ci):
#   srcs = source_services_in_cluster(ci)
#   cluster_dependent_services = set()
#   for src in srcs:
#     deps = set(full_map[TOPOLOGY_KEY][src]["dep"])
#     cluster_dependent_services |= deps
#
#   return list(cluster_dependent_services)
#
# def service_locations(s):
#   clusters = full_map[TOPOLOGY_KEY][s]["clusters"]
#   return list(map(lambda ci: "{}.{}".format(s,ci), clusters))
#
# # Cost
# def price_cost(Sk, cv, sj, ci):
#   total_price = full_map["Cost"]["Cluster2ClusterPricing"]
#   return
