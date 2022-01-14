import time, random, math, yaml
import networkx as nx
from utils.helpers import load_ymal

def get_all_dependent_services(service_name, dep_dict):
  # print("lookup for {} dependents".format(service_name))
  dependant_services = []
  for name, data in dep_dict.items():
    if service_name in data["dependencies"]:
      # print("{} IS dependent of {}".format(name, service_name))
      dependant_services.append(name)
    # else:
      # print("{} IS NOT dependent of {}".format(name, service_name))
  return dependant_services

def get_dependencies_dict(G):
  assert(nx.algorithms.dag.is_directed_acyclic_graph(G))

  services = nx.convert.to_dict_of_dicts(G)
  yaml_ready_service = {}

  for svc_name, dependencies in services.items():
    # If in_degree == 0 this is the first service in line, i.e front end, else it is some internal service
    label = "internal"
    in_degree = G.in_degree(svc_name)
    if in_degree == 0:
      label = "front-end"
    # Dependencies
    d = {}
    for dependency in dependencies:
      d["{}".format(dependency)] = {
          "name": "{}".format(dependency),
          "req_size": 50
      }
    # yaml
    yaml_ready_service["{}".format(svc_name)] = {
        "name": "{}".format(svc_name),
        "label": label,
        "expected-outbound-req-size-kb": 50,
        "dependencies": d
    }

  return yaml_ready_service

def simulate_dag(
    min_per_rank = 1, max_per_rank = 5, # Nodes/Rank: How 'fat' the DAG should be.
    min_ranks = 2, max_ranks = 5, # Ranks: How 'tall' the DAG should be
    edge_prob = 0.3 # Chance of having an Edge
  ):
  nodes = random.randint(3,20)
  G = nx.gnp_random_graph(nodes, 0.5, directed=True)
  G = nx.DiGraph([(u,v) for (u,v) in G.edges() if u<v])
  assert(nx.algorithms.dag.is_directed_acyclic_graph(G))
  return G
  G = nx.DiGraph()
  nodes = 0
  ranks = min_ranks + (random.randrange(100_000) % (max_ranks - min_ranks + 1))
  
  nodes_added_to_graph = set()
  for r in range(ranks):
    # New nodes of 'higher' rank than all nodes generated till now.
    new_nodes = min_per_rank + (random.randrange(100_000) % (max_per_rank - min_per_rank + 1))
    # Edges from old nodes ('nodes') to new ones ('new_nodes').
    for node in range(nodes):
      if node not in nodes_added_to_graph:
        G.add_node(node)
        nodes_added_to_graph.add(node)

      for new_node in range(new_nodes):
        new_node = new_node+nodes
        if new_node not in nodes_added_to_graph:
          G.add_node(new_node)
          nodes_added_to_graph.add(new_node)

        if random.randrange(100) / 100 >= edge_prob: # Add an Edge
          G.add_edge(node, new_node)

    nodes += new_nodes # Accumulate into old node setc

  assert(nx.algorithms.dag.is_directed_acyclic_graph(G))
  return G

# Random
def randomize_service_instance_count(max_count):
  return random.randint(1,max_count)

def randomize_service_instance_placement(count, clusters):
  assert(count <= len(clusters))
  return random.sample(clusters, k=count)

# Getters
def _services_by_label(dependency_dict, label):
  services = []
  for svc_name, data in dependency_dict.items():
    if data["label"] == label:
      services.append(svc_name)
  return services

def _internal_service(dependency_dict):
  return _services_by_label(dependency_dict, "internal")

def _fe_services(dependency_dict):
  return _services_by_label(dependency_dict, "front-end")

# Generators
def generate_topology_skeleton(by_clusters):
  yaml_ready_topology = {}
  for cluster in by_clusters:
    yaml_ready_topology[cluster] = {
        "services": {}
    }
  
  return yaml_ready_topology

# Assigners
def assign_service(service, to_cluster, with_capacity, in_topology):
  in_topology[to_cluster]["services"][service] = {
    "name": service,
    "rps_capacity": with_capacity
  }

def assign_fe_services(fe_services, clusters, topology):
  for svc in fe_services:
    for cluster in clusters:
      assign_service(svc, cluster, 30_000, topology)

def assign_internal_services(internal_services, clusters, topology):
  # Assign services with zerp capacity, update capacity after assignment
  for svc in internal_services:
    svc_instance_count = randomize_service_instance_count(len(clusters))
    svc_placements = randomize_service_instance_placement(svc_instance_count, clusters)
    for cluster in svc_placements:
      assign_service(svc, cluster, 0, topology)


# Patchers
def _get_instance_locations(service, topology):
  clusters = []
  for cluster_name, cluster_data in topology.items():
    for svc_name, svc_data in cluster_data["services"].items():
      if svc_name != service:
        continue
      clusters.append(cluster_name)
  return clusters

def _get_instance_count(service, topology):
  count = 0
  for _, cluster_data in topology.items():
    for svc_name, svc_data in cluster_data["services"].items():
      if svc_name != service:
        continue
      count+=1
  return count

def _get_capacity(service, topology):
  capacity = 0
  for _, cluster_data in topology.items():
    for svc_name, svc_data in cluster_data["services"].items():
      if svc_name != service:
        continue
      cap = svc_data["rps_capacity"]
      # if cap is None or cap == 0:
      #   raise
      capacity+=cap
  return capacity

def _random_list(m, n):
  min_cap = math.ceil(n*0.1)
  # print("m = {}\nn = {}\nmin = {}".format(m,n,min_cap))
  res = [0] * m
  for i in range(n) :
      # Increment any random element, from the array by 1
      res[random.randint(min_cap, n) % m] += 1
  return res

def update_internal_services_capacity(G, dep_dict, topology):
  # Update capacity
  sources = []
  for u,_ in G.nodes(data=True):
    if G.in_degree(u) == 0:
      sources.append(u)

  for src in sources:
    # print("bfs for", src)
    for src_node, dst_node in nx.bfs_edges(G, src):
      if src != src_node:
        print("src{} != src_node{}".format(src, src_node))
      # print("src node = {}\ndst_node = {}".format(src_node, dst_node))
      dst_node = str(dst_node)
      # We need to calc cap for the dst node
      dependents = get_all_dependent_services(dst_node, dep_dict)
      if len(dependents) == 0: # We are at source, i.e front-end we already set capacity
        # print("1 skipping {}".format(dst_node))
        continue
      
      total_cap_of_dependents = int(sum([_get_capacity(dep_svc, topology) for dep_svc in dependents]) * 1.05)
      instance_count = _get_instance_count(dst_node, topology)
      # print("updating capacity for {} as its total load is {} and its instance count is {}".format(dst_node, total_cap_of_dependents, instance_count))
      capacities = _random_list(instance_count, total_cap_of_dependents)
      clusters = _get_instance_locations(dst_node, topology)
      for cluster, cap in zip(clusters, capacities):
        assign_service(dst_node, cluster, cap, topology)


def new_generator():
  G = simulate_dag()
  data_centers = list(map(lambda x: x[0], load_ymal("yamls/datacenters.yml").items()))
  # One cluster pr DC at least 3 clusters
  clusters = random.choices(data_centers, k=random.randint(3, len(data_centers))) 

  topology_skeleton = generate_topology_skeleton(clusters)
  services_dict = get_dependencies_dict(G)

  fe_services = _fe_services(services_dict)
  assign_fe_services(fe_services, clusters, topology_skeleton)

  int_services = _internal_service(services_dict)
  assign_internal_services(int_services, clusters, topology_skeleton)

  update_internal_services_capacity(G, services_dict, topology_skeleton)

  data = {
            "app-topology": topology_skeleton,
            "services": services_dict
        }
  with open('yamls/application_ymals/random/{}.yml'.format(time.time()), 'w') as outfile:
      yaml.dump(data, outfile, default_flow_style=False)


if __name__ == '__main__':
    for _ in range(5):
      new_generator()