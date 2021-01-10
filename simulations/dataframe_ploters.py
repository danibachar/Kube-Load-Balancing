import numpy as np
import pandas as pd

from utils.plots import plot_avg, full_plot, bar_plot

def plot(dfs):

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
        for type, t_dfs in df_type_map.items():
            bars_names[-1].append(type)
            concated_df = pd.concat(t_dfs.values())
            total_traffic_cost_in_usd[-1].append(concated_df["cost_in_usd"].sum())
            total_traffic_sent_in_gb[-1].append(concated_df["size_in_gb"].sum())
            avg_latencies[-1].append(concated_df["zone_dependent_latency"].mean())
            job_durations[-1].append(concated_df["duration"].mean())
            total_jobs_handled[-1].append(len(concated_df.index))

    total_traffic_cost_in_usd = np.mean(total_traffic_cost_in_usd, axis=0)
    total_traffic_sent_in_gb = np.mean(total_traffic_sent_in_gb, axis=0)
     # = total_traffic_cost_in_usd/total_traffic_sent_in_gb
    total_jobs_handled = np.mean(total_jobs_handled, axis=0)
    avg_latencies = np.mean(avg_latencies, axis=0)
    job_durations = np.mean(job_durations, axis=0)

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
            latency = lat,
            max_latency = max_latency
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
