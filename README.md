# Kube-Load-Balancing
Simple Repository for simulating different Multi-Cluster scenarios.

# Installation

1. `python -m venv venv`
1. `source ./venv/bin/activate` (Linux, macOS) or `./venv/Scripts/activate` (Win)
1. `pip install -e .`
See [link](https://stackoverflow.com/questions/6323860/sibling-package-imports) for more details


## Materails

Bin packing - https://www.cs.huji.ac.il/~ai/projects/old/binPacking2.pdf

Bin packing with general cost structure - http://math.haifa.ac.il/lea/GCBP.pdf

The Price of Clustering in Bin-Packing with Applications to Bin-Packing with Delays - https://yemek.net.technion.ac.il/files/poc.pdf

The Maximum Resource Bin Packing Problem - http://math.haifa.ac.il/lea/lbp.pdf

Bin covering - like bin packing but with finite bin count

## Pricing

- GCP:
  - https://cloud.google.com/vpc/network-pricing#internet_egress

- AWS:
  - https://aws.amazon.com/ec2/pricing/on-demand/#Data_Transfer


## Latency

- GCP:
  - https://docs.aviatrix.com/HowTos/gcp_inter_region_latency.html#:~:text=Google%20Cloud%20supports%2018%20regions,servers%20in%20two%20different%20regions.
  - https://geekflare.com/google-cloud-latency/
  - https://datastudio.google.com/u/0/reporting/fc733b10-9744-4a72-a502-92290f608571/page/70YCB

- AWS:

- Comparison:
  - https://medium.com/@sachinkagarwal/public-cloud-inter-region-network-latency-as-heat-maps-134e22a5ff19
  - https://pc.nanog.org/static/published/meetings/NANOG75/1909/20190218_Kesavan_Comparing_The_Network_v1.pdf
  - https://www.cockroachlabs.com/blog/aws-azure-gcp-respond-to-the-2020-cloud-report/


## YMAL Resources:

- datacenters.yml:
  - https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html
  - https://cloud.google.com/compute/docs/regions-zones
