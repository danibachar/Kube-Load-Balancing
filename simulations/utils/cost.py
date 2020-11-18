

# Each criteria get equal weight for now

def simple_addative_weight(price, latency, min_price, min_latency):
    return (min_price/price)*0.5 + (min_latency/latency)*0.5
