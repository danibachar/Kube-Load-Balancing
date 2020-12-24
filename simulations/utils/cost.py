import pandas as pd

# Each criteria get equal weight for now
def simple_min_addative_weight(
    price,
    min_price,
    latency,
    min_latency
):
    price_part = 0
    if price > 0:
        price_part = (min_price/price)*0.5

    latency_part = 0
    if latency > 0:
        latency_part = (min_latency/latency)*0.5

    return price_part + latency_part

def simple_max_addative_weight(
    price,
    max_price,
    latency,
    max_latency
):
    if max_price == 0:
        raise
    if max_latency == 0:
        raise

    price_part = (price / max_price) * 0.5
    latency_part = (latency / max_latency) * 0.5

    return price_part + latency_part
