import matplotlib.pyplot as plt

def plot(times, costs, loads, cost_title="", loads_title="", scale_cost_axis=False):
    fig, ax1 = plt.subplots()

    ax1.set_title(cost_title)

    ax1.set_xlabel('time (min)')

    color = 'tab:red'
    ax1.set_ylabel('cost', color=color)
    ax1.plot(times, costs, color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    if scale_cost_axis:
        ax1.set_ylim([min(costs)*-2, max(costs)*2])

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    ax2.set_title(loads_title)

    color = 'tab:blue'
    ax2.set_ylabel('load', color=color)  # we already handled the x-label with ax1
    ax2.plot(times, loads, color=color)
    ax2.tick_params(axis='y', labelcolor=color)


    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()
