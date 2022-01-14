import pandas as pd

# Each criteria get equal weight for now
def simple_min_addative_weight(
    price,
    min_price,
    price_weight,
    latency,
    min_latency,
    latency_weight
):
    price_part = 0
    if price > 0:
        price_part = (min_price/price)*price_weight

    latency_part = 0
    if latency > 0:
        latency_part = (min_latency/latency)*latency_weight

    return price_part + latency_part

def simple_max_addative_weight(
    price,
    max_price,
    price_weight,
    latency,
    max_latency,
    latency_weight
):
    if max_price == 0:
        if price == 0:
            price = max_price = 1
        else:
            raise Exception("max_price == 0")
    if max_latency == 0:
        if latency == 0:
            latency = max_latency = 1
        else:
            raise Exception("max_latency == 0")

    price_part = (price / max_price) * price_weight
    latency_part = (latency / max_latency) * latency_weight

    return price_part + latency_part
