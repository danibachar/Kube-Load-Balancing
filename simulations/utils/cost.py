

# Each criteria get equal weight for now

def simple_addative_weight(price, latency, min_price, min_latency):
    price_part = 0
    if price > 0:
        price_part = (min_price/price)*0.5

    latency_part = 0
    if latency > 0:
        latency_part = (min_latency/latency)*0.5

    return price_part + latency_part
