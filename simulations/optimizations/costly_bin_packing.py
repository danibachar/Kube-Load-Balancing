from __future__ import print_function
from ortools.linear_solver import pywraplp
from pulp import *
import time

def create_data_model():
    """Create the data for the example."""
    data = {}
    weights = [1,1,1,1,2] # Load job impose
    data['weights'] = weights
    data['items'] = list(range(len(weights)))
    data['num_items'] = len(weights)
    num_bins = 3
    data['bins'] = list(range(num_bins))
    data['bins_costs'] = [20,30,40]
    data['bin_capacities'] = [1,2,3]
    return data




def ortools_main():
    data = create_data_model()

    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver('SCIP')

    # Variables
    # x[i, j] = 1 if item i is packed in bin j.
    pr = {}
    x = {}
    for j in data['bins']:
        for i in data['items']:
            x[(i, j)] = solver.IntVar(0, 1, 'x_%i_%i' % (i, j))

    # Constraints
    # Each item can be in at most one bin.
    for i in data['items']:
        solver.Add(sum(x[i, j] for j in data['bins']) == 1)
        # solver.Add(sum(x[i, j] for j in data['bins']) >= 1)
        # solver.Add(sum(x[i, j] for j in data['bins']) >= 0.001)
        # for j in data['bins']:
        #     solver.Add(x[i, j] >= 0.1)
    # The amount packed in each bin cannot exceed its capacity.
    for j in data['bins']:
        solver.Add(
            sum(x[(i, j)] * data['weights'][i]
                for i in data['items']) <= data['bin_capacities'][j])

    # Objective
    objective = solver.Objective()
    for j in data['bins']:
        for i in data['items']:
            objective.SetCoefficient(x[(i, j)], data['bins_costs'][j])
    objective.SetMinimization()

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print('Total packed cost:', objective.Value())
        total_weight = 0
        for j in data['bins']:
            bin_weight = 0
            bin_value = 0
            print('Bin ', j, '\n')
            for i in data['items']:
                if x[i, j].solution_value() > 0:
                    print('Item', i, '- weight:', data['weights'][i], ' bins_costs:',
                          data['bins_costs'][j])
                    bin_weight += data['weights'][i]
                    bin_value += data['bins_costs'][j]
            print('Packed bin weight:', bin_weight)
            print('Packed bins_costs:', bin_value)
            print()
            total_weight += bin_weight
        print('Total packed weight:', total_weight)
    else:
        print('The problem does not have an optimal solution.')

def pulp_main():
    # Based - https://github.com/mbasilyan/binpacking/blob/master/binpacker.py
    #
    # A list of item tuples (name, weight) -- name is meaningless except to humans.
    # Weight and Size are used interchangeably here and elsewhere.
    #
    items = [("j_1",2),
             # ("j_2", 2),
             # ("j_3", 1),
             # ("j_4", 1),
             # ("j_5", 1),
             # ("j_6", 1),
             # ("j_7", 1),
             ]

    itemCount = len(items)

    bins_cap = [
        ("b_1", 1),
        ("b_2", 2),
        ("b_3", 3),
    ]

    costs = [
        ("b_1", 10),
        ("b_2", 20),
        ("b_3", 30),
    ]

    binsCount = len(bins_cap)
    # An indicator variable that is assigned 1 when item is placed into binNum
    possible_ItemInBin = [(itemTuple[0], binNum) for itemTuple in items
                                                for binNum in range(binsCount)]
    x = pulp.LpVariable.dicts('itemInBin', possible_ItemInBin,
                                lowBound = 0,
                                upBound = 1)

    print(x)
    # Initialize the problem
    prob = LpProblem("Bin Packing Problem", LpMinimize)

    # Add the objective function.
    # for i in range(binsCount): .
    prob += lpSum([x[(items[j][0], i)] * costs[i][1] for j in range(itemCount) for i in range(binsCount)])#, ("Objective: Minimize cost of assigning jobs to "+bins_cap[i][0])


    # First constraint: For every item, the sum of bins in which it appears must be 1
    for j in items:
        prob += lpSum([x[(j[0], i)] for i in range(binsCount)]) == 1, ("An item can be in only 1 bin -- " + str(j[0]))

    # Second constraint: For every bin, the number of items in the bin cannot exceed the bin capacity
    for i in range(binsCount):
        prob += lpSum([items[j][1] * x[(items[j][0], i)] for j in range(itemCount)]) <= bins_cap[i][1], ("The sum of item sizes must be smaller than the bin -- " + str(i))

    # Write the model to disk
    prob.writeLP("BinPack.lp")

    # Solve the optimization.
    start_time = time.time()
    prob.solve()
    print("Solved in %s seconds." % (time.time() - start_time))

    # Bins used
    # print("Bins used: " + str(sum(([y[i].value() for i in range(maxBins)]))))

    # The rest of this is some unpleasent massaging to get pretty results.
    bins = {}
    print(x)
    for itemBinPair in x.keys():
        if(x[itemBinPair].value() == 1):
            itemNum = itemBinPair[0]
            binNum = itemBinPair[1]
            if binNum in bins:
                bins[binNum].append(itemNum)
            else:
                bins[binNum] = [itemNum]
    total_cost = 0
    print("bins", bins)
    for b in bins.keys():
        print(str(b) + ": " + str(bins[b]))
        total_cost+=costs[b][1]*len(bins[b])
    print("total cost = ", total_cost)

def pulp_next_try():
    job_loads = [1,2,1,2,1]
    jobs = ["j"+str(j) for j in range(len(job_loads))]

    clusters = ["c1", "c2", "c3"]
    cluster_costs = [10, 20, 30]
    cluster_cap = [1,2,3]

    prob = LpProblem("Service Selection Problem", LpMinimize)

    x = []
    for cluster_idx in range(len(clusters)):
        x.append([])
        for job_idx in range(len(jobs)):
            name = jobs[job_idx]+"_"+clusters[cluster_idx]
            var = pulp.LpVariable(name, lowBound = 0, upBound = 1, cat='Integer')
            x[cluster_idx].append(var)
    prob += lpSum( x[cluster_idx][job_idx] * cluster_costs[cluster_idx] for job_idx in range(len(jobs)) for cluster_idx in range(len(clusters)) )
    # A job must be assigned to one clsuter only
    for job_idx in range(len(jobs)):
        prob += lpSum([x[cluster_idx][job_idx] for cluster_idx in range(len(clusters))]) == 1

    # A cluster cannot handle more of its cap
    for cluster_idx in range(len(clusters)):
        prob += lpSum([x[cluster_idx][job_idx] * job_loads[job_idx] for job_idx in range(len(jobs))]) <= cluster_cap[cluster_idx]

    prob.writeLP("ServiceSelection.lp")
    prob.solve()
    print(prob.status)
    total_cost = 0
    cluster_load_dist = []
    for cluster_idx in range(len(clusters)):
        cluster_load_dist.append(0)
        for job_idx in range(len(jobs)):
            is_job_assigned_to_cluster = x[cluster_idx][job_idx].value()
            cluster_load_dist[cluster_idx]+=is_job_assigned_to_cluster
            print(str(x[cluster_idx][job_idx]) + " = " + str(is_job_assigned_to_cluster))
            total_cost+= is_job_assigned_to_cluster * cluster_costs[cluster_idx]
    print("cluster_load_dist = ",cluster_load_dist)
    print("total cost = ", total_cost)
if __name__ == '__main__':
    # pulp_main()
    pulp_next_try()
