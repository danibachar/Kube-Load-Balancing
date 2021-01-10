import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import lfilter

from utils.plots import plot_avg, full_plot, bar_plot
from utils.cost import simple_max_addative_weight

def _build_comparison_map(dfs):
    comparisons = {}
    for iteration, iteration_dfs in dfs.items():
        for func, df in iteration_dfs.items():
            if comparisons.get(func, None) is None:
                comparisons[func] = pd.concat(df.values())
            else:
                comparisons[func] = pd.concat([comparisons[func]] + list(df.values()))

    return comparisons

def _plot_service_loads(dfs):
    # load
    _dfs = []
    for key, df in dfs.items():
        df["load_balance"] = key
    dfs = pd.concat(dfs)
    n = 20  # the larger n is, the smoother curve will be
    b = [1.0 / n] * n
    a = 1

    plots_count = 0
    dfs = dfs[dfs["job_type"] != "product_page"]
    for groups in dfs.groupby(["job_type", "target_zone_id"]):
        plots_count+=1
    fig, axs  = plt.subplots(int(plots_count/3), 3)
    for groups in dfs.groupby(["job_type", "target_zone_id"]):
        table_name = groups[0]
        g_df = groups[1]
        plots_count-=1
        w = 1
        markers = ["h","v","o"]
        linestyles = ["-","--",":"]
        alphas = [0.3,0.6, 1]
        for group in g_df.groupby("load_balance"):
            name = group[0]
            df = group[1]
            y = lfilter(b, a, df["load"].to_list())
            x = df["arrival_time"].to_list()
            axs[int(plots_count/3), plots_count%3].plot(x, y, label = name, linewidth=1, linestyle=linestyles[w-1])
            w+=1

        axs[int(plots_count/3), plots_count%3].set_title(table_name)
    plt.legend()
    plt.subplots_adjust(hspace=0.5)
    plt.show()

def _plot_bars(dfs ,type="mean"):

    total_traffic_cost_in_usd = []
    bars_names = []
    total_traffic_sent_in_gb = []
    total_jobs_handled = []
    avg_latencies = []
    job_durations = []

    for iter, df_type_map in dfs.items():
        bars_names.append([])
        total_traffic_cost_in_usd.append([])
        total_traffic_sent_in_gb.append([])
        total_jobs_handled.append([])
        avg_latencies.append([])
        job_durations.append([])
        for lb_type, t_dfs in df_type_map.items():
            bars_names[-1].append(lb_type)
            concated_df = pd.concat(t_dfs.values())
            total_traffic_cost_in_usd[-1].append(concated_df["cost_in_usd"].sum())
            total_traffic_sent_in_gb[-1].append(concated_df["size_in_gb"].sum())
            avg_latencies[-1].append(concated_df["zone_dependent_latency"].mean())
            job_durations[-1].append(concated_df["duration"].mean())
            total_jobs_handled[-1].append(len(concated_df.index))
    if type == "median":
        total_traffic_cost_in_usd = np.median(total_traffic_cost_in_usd, axis=0)
        total_traffic_sent_in_gb = np.median(total_traffic_sent_in_gb, axis=0)
        total_jobs_handled = np.median(total_jobs_handled, axis=0)
        avg_latencies = np.median(avg_latencies, axis=0)
        job_durations = np.median(job_durations, axis=0)
    elif type == "mean":
        total_traffic_cost_in_usd = np.mean(total_traffic_cost_in_usd, axis=0)
        total_traffic_sent_in_gb = np.mean(total_traffic_sent_in_gb, axis=0)
        total_jobs_handled = np.mean(total_jobs_handled, axis=0)
        avg_latencies = np.mean(avg_latencies, axis=0)
        job_durations = np.mean(job_durations, axis=0)
    elif isinstance(type, float):
        total_traffic_cost_in_usd = np.quantile(total_traffic_cost_in_usd, type, axis=0)
        total_traffic_sent_in_gb = np.quantile(total_traffic_sent_in_gb, type, axis=0)
        total_jobs_handled = np.quantile(total_jobs_handled, type, axis=0)
        avg_latencies = np.quantile(avg_latencies, type, axis=0)
        job_durations = np.quantile(job_durations, type, axis=0)
    else:
        print("type", type)
        raise
    title = "Traffic Analysis\n"
    bar_titles = []
    bar_improvments = []

    scatter_titles = []
    scatter_improvments = []

    line_titles = []
    line_values = []
    line_improvments = []

    job_duration_titles = []
    job_duration_improvments = []

    avg_price_per_gb = []

    max_price_per_gb = max(np.array(total_traffic_sent_in_gb)/np.array(total_traffic_cost_in_usd))
    max_latency = max(avg_latencies)
    min_price_per_gb = min(np.array(total_traffic_sent_in_gb)/np.array(total_traffic_cost_in_usd))
    min_latency = min(avg_latencies)
    for i in range(len(total_traffic_sent_in_gb)):
        # Traffic titles - Bars
        egress = total_traffic_sent_in_gb[i]
        cost = total_traffic_cost_in_usd[i]
        jobs = total_jobs_handled[i]
        lat = avg_latencies[i]
        job_dur = job_durations[i]

        job_duration_titles.append('%.3f' % job_dur + "ms")
        if i > 0:
            percent_improvment = ((job_durations[i-1]-job_durations[i]) / job_durations[i-1]) * 100
            pt = ('%.3f' % percent_improvment)
            job_duration_improvments.append("{} %\nimprovment".format(pt))
        else:
            job_duration_improvments.append("")
        avg_price = cost/egress
        avg_price_per_gb.append(avg_price)

        line_values.append(simple_max_addative_weight(
            price = avg_price,
            max_price = max_price_per_gb,
            price_weight=0.5,
            latency = lat,
            max_latency = max_latency,
            latency_weight=0.5,
        ))
        line_titles.append("Cost = "+'%.3f' % line_values[-1])
        if i > 0:
            percent_improvment = ((line_values[i-1]-line_values[i]) / line_values[i-1]) * 100
            pt = ('%.3f' % percent_improvment)
            line_improvments.append("{} %\nimprovment".format(pt))
        else:
            line_improvments.append("")

        if i == 0:
            title += "Egress = {}GB, Jobs Count = #{}".format("%.3f"%egress, int(jobs))

        bar_title = "Payment = {}$\nGB Price = {}$".format("%.3f"%cost,"%.3f"%(cost/egress))
        if i > 0:
            percent_improvment = ((total_traffic_cost_in_usd[i-1]-total_traffic_cost_in_usd[i]) / total_traffic_cost_in_usd[i-1]) * 100
            pt = ('%.3f' % percent_improvment)
            bar_improvments.append("{} %\nimprovment".format(pt))
        else:
            bar_improvments.append("")
        bar_titles.append(bar_title)
        # Latency titles - Scatter
        l_title = "Latency {}ms".format('%.3f' %lat)
        if i > 0:
            percent_improvment = ((avg_latencies[i-1]-avg_latencies[i]) / avg_latencies[i-1]) * 100
            pt = ('%.3f' % percent_improvment)
            scatter_improvments.append("{} %\nimprovment".format(pt))
        else:
            scatter_improvments.append("")
        scatter_titles.append(l_title)

    bar_plot(
        x_values=bars_names[0],

        bars_values=avg_price_per_gb,
        bar_titles=bar_titles,
        bar_improvments=bar_improvments,

        scatter_values=avg_latencies,
        scatter_titles=scatter_titles,
        scatter_improvments=scatter_improvments,

        line_values=line_values,
        line_titles=line_titles,
        line_improvments=line_improvments,

        job_duration_values=job_durations,
        job_duration_titles=job_duration_titles,
        job_duration_improvments=job_duration_improvments,

        # title=title
    )

def plot_dfs(dfs):
    types = ["mean"]#, "median",0.9, 0.95, 0.99, ]
    for app_name, app_testing_dfs in dfs.items():
        print("app name", app_name)
        comparisons = _build_comparison_map(app_testing_dfs)
        _plot_service_loads(comparisons)
        for type in types:
            _plot_bars(app_testing_dfs, type=type)


    # # plot density function
    # import matplotlib.pyplot as plt
    # m = 27_000
    # a = 10
    # # s = heavy_tail_jobs_distribution("pareto", 1000, m)
    # s = (np.random.pareto(a, size = 500) + 1) * m
    # print("DB: - s = ",s)
    # print("DB: - avg = ",np.average(s, axis=0))
    # count, bins, _ = plt.hist(s, 100, density=True)
    # fit = a*m**a / bins**(a+1)
    # plt.plot(bins, max(count)*fit/max(fit), linewidth=2, color='r')
    # plt.xlabel('RPS')
    # plt.ylabel('Pr(RPS=x)')
    # plt.show()
