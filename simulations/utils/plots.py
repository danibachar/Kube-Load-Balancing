import matplotlib.pyplot as plt
import random
from scipy.signal import savgol_filter
import numpy as np

def rand_hex():
    return "#"+"%06x" % random.randint(0, 0xFFFFFF)

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

def plot_avg(costs, times, loads, title_prefix=""):
    if len(costs) == 0:
        return
    total_cost = sum(costs)
    cost_title = "total cost = {}".format(total_cost)
    plot(
        costs = costs,
        times = times,
        loads = loads,
        cost_title = title_prefix + " " + cost_title
    )


def _dynamic_plots(x_values, x_title, y_values_subsets, y_labels, title):
    if len(x_values) == 0:
        assert()
    if len(y_values_subsets) == 0:
        assert()
    if len(y_values_subsets) != len(y_labels):
        assert()

    fig, ax1 = plt.subplots()
    ax1.set_title(title)

    ax1.set_xlabel(x_title)

    y_subset_count = len(y_values_subsets)
    # First Y - a must
    values = y_values_subsets[0]
    label = y_labels[0]
    color = 'tab:red'
    ax1.set_ylabel(label, color=color)
    ax1.plot(x_values, values, color=color, alpha=0.7, linewidth=5.0)
    ax1.tick_params(axis='y', labelcolor=color)

    colors = ['tab:blue', 'tab:green']

    for yi in range(1, y_subset_count):
        print("yi", yi)
        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

        values = y_values_subsets[yi]
        label = y_labels[yi]
        print("loop labe", label)
        color = colors[yi-1]#rand_hex()

        # if yi == 1:
        # #     ax2.set_title(label)
        #     ax2.set_ylabel(label, col or=color)
        #     ax2.tick_params(axis='y', labelcolor=color)
        # else:
        count = 0
        for i,j in zip(x_values, values):
            if count % 5 == 0:
                ax2.annotate(("%.4f" % j),xy=(i,j),textcoords="offset points", xytext=(0,10),ha='center',rotation='vertical')
            count+=1

        ax2.plot(
            x_values,
            values,
            color=color,
            alpha=1.0,
            linewidth=2.0,
            label=label,
            marker='h',
            markevery=5
        )
        ax2.set_yticklabels([])



    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()

def full_plot(traffic_costs, avg_latency, loads, times, title_prefix):

    # Graph bases
    fig, ax1 = plt.subplots()
    ax1.set_title(title_prefix + "performance")
    ax1.set_xlabel("time (sec)")

    # Load left Y axis
    color = 'tab:red'
    title = "total RPS handeled = {}".format(sum(loads))
    ax1.set_ylabel(title, color=color)
    ax1.plot(times, loads, color=color, alpha=0.7,linewidth=5.0)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    # Traffic Pricing Right Y axis
    color = 'tab:blue'
    title = "total traffic payment = {}".format(sum(traffic_costs))
    ax2.set_ylabel(title, color=color)
    ax2.plot(times, traffic_costs, color=color, alpha=1.0, linewidth=1.0)
    ax2.tick_params(axis='y', labelcolor=color)

    ax3 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    # Latency with markers
    avg_latency = savgol_filter(avg_latency, 51, 3)
    color = 'tab:green'
    ax3.plot(
        times,
        avg_latency, # window size 51, polynomial order 3
        color=color,
        alpha=1.0,
        linewidth=2.0,
        marker='h',
        markevery=5
    )
    count = 0
    for i,j in zip(times, avg_latency):
        if count % 5 == 0:
            ax3.annotate(("%.4f" % j),xy=(i,j),textcoords="offset points", xytext=(0,10),ha='center',rotation='vertical')
        count+=1
    ax3.set_yticklabels([])

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()

def bar_plot(
    x_values=[],

    bars_values=[],
    bar_titles=[],
    bar_improvments=[],
    bars_title="Avg Price per GB",#"Total Traffic Pricing",
    bars_y_label="$",

    scatter_values=[],
    scatter_titles=[],
    scatter_improvments=[],
    scatter_title="Avg Latency per request",
    scatter_y_label="ms",

    line_values=[],
    line_titles=[],
    line_improvments=[],
    line_title="Avarage Cost",
    line_y_label="",

    job_duration_values=[],
    job_duration_titles=[],
    job_duration_improvments=[],
    job_duration_title="Avg Job Duration",
    job_duration_y_label="ms",

    title=""
):
    x = np.arange(len(x_values))  # the label locations
    fig, axs = plt.subplots(3)
    fig.suptitle(title)

    axs[0].bar(x, bars_values ,color = 'red')
    axs[0].set_xticks(x)
    axs[0].set_xticklabels(x_values)
    axs[0].set_title(bars_title)
    axs[0].set_ylabel(bars_y_label)
    axs[0].set_ylim([0, max(bars_values)*1.25])

    for i, value in enumerate(bars_values):
    #     text = bar_titles[i]+"\n"+bar_improvments[i]
        axs[0].text(x[i], value, str(round(value,3)), color = 'black', ha='center')

    axs[1].bar(x, scatter_values,color = 'blue')
    axs[1].set_xticks(x)
    axs[1].set_xticklabels(x_values)
    axs[1].set_title(scatter_title)
    axs[1].set_ylabel(scatter_y_label)
    axs[1].set_ylim([0, max(scatter_values)*1.25])

    for i, value in enumerate(scatter_values):
    #     text = scatter_titles[i]+"\n"+scatter_improvments[i]
        axs[1].text(x[i], value, str(round(value,3)), color = 'black', ha='center')

    # axs[2].bar(x, line_values,color = 'green')
    # axs[2].set_xticks(x)
    # axs[2].set_xticklabels(x_values)
    # axs[2].set_title(line_title)
    # axs[2].set_ylabel(line_y_label)
    # axs[2].set_ylim([0, max(line_values)*1.25])
    #
    # for i, value in enumerate(line_values):
    # #     text = line_titles[i]+"\n"+line_improvments[i]
    #     axs[2].text(x[i], value, str(round(value,3)), color = 'black', ha='center')

    axs[2].bar(x, job_duration_values, color = 'purple')
    axs[2].set_xticks(x)
    axs[2].set_xticklabels(x_values)
    axs[2].set_title(job_duration_title)
    axs[2].set_ylabel(job_duration_y_label)
    axs[2].set_ylim([0, max(job_duration_values)*1.25])
    for i, value in enumerate(job_duration_values):
        # text = job_duration_titles[i]+"\n"+job_duration_improvments[i]
        axs[2].text(x[i], value, str(round(value,3)), color = 'black', ha='center')

    plt.subplots_adjust(hspace=0.5)

    plt.show()
