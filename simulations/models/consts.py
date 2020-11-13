
bookinfo_application_location_graph = {
    "services_config": {
        "product_page": {
            "dependencies": ["review1", "review2", "review3", "details"],
            "incoming_req_size": 100, # in KB
        },
        "review1": {
            "dependencies": [],
            "incoming_req_size": 400, # in KB
        },
        "review2": {
            "dependencies": ["raiting"],
            "incoming_req_size": 450, # in KB
        },
        "review3": {
            "dependencies": ["raiting"],
            "incoming_req_size": 350, # in KB
        },
        "details": {
            "dependencies": [],
            "incoming_req_size": 250, # in KB
        },
        "raiting": {
            "dependencies": [],
            "incoming_req_size": 200, # in KB
        },
    },
    "locations": ["aws-us-east", "gcp-us-west", "gcp-eu-zurich", "aws-brazil-saopaulo", "gcp-ociana-sydney"],
    "pricing": { # Per GB
        "internet": 0.09,
        "cross-region": 0.02,
        "cross-zone": 0.01,
    },
    "clusters": {
        "aws-us-east": {
            "services": [("product_page", 50), ("review1",150), ("review2",100), ("details",150)], # capacity
            "latency": { # in ms
                "gcp-us-west": 100,
                "gcp-eu": 200,
                "aws-south-brazil": 150,
                "gep-ociana-sydney": 300
            }
        },
        "gcp-us-west": {
            "services": [("product_page", 50), ("review2", 100), ("raiting", 200)],
            "latency": {
                "aws-us-east": 100,
                "gcp-eu": 250,
                "aws-south-brazil": 150,
                "gep-ociana-sydney": 300
            }
        },
        "gcp-eu-zurich": {
            "services": [("product_page", 50), ("review1", 150), ("details",100), ("raiting", 175)],
            "latency": {
                "aws-us-east": 150,
                "gcp-us-west": 250,
                "aws-south-brazil": 150,
                "gep-ociana-sydney": 300
            }
        },
        "aws-brazil-saopaulo": {
            "services": [("product_page", 50), ("review2", 100), ("review3",200), ("raiting", 175)],
            "latency": {
                "aws-us-east": 150,
                "gcp-us-west": 100,
                "gcp-eu": 200,
                "gep-ociana-sydney": 300
            }
        },
        "gcp-ociana-sydney":{
            "services": [("product_page", 50), ("review3",100), ("details", 50), ("raiting", 50)],
            "latency": {
                "aws-us-east": 150,
                "gcp-us-west": 100,
                "gcp-eu": 200,
                "aws-south-brazil": 150,
            }
        },
    },

}

base_topology_map = {
    "aws": {
        "pricing": {
            "internet": 0.09,
            "cross-region": 0.02,
            "cross-zone": 0.01,
        },
        "regions": {
            "us": {
                "east": {
                    "ohio": {
                        "zones": ["1", "2", "3"]
                    },
                },
                "west": {
                    "oregon": {
                        "zones": ["1", "2", "3"]
                    },
                },
            },
            "emea": {
                "europe": {
                    "ireland": {
                        "zones": ["1", "2", "3"]
                    },
                },
                "middle-east": {
                    "baharain": {
                        "zones": ["1", "2", "3"]
                    },
                },
                "africa": {
                    "cape-town": {
                        "zones": ["1", "2", "3"]
                    },
                },
            },
            "asia-pasific": {
                "ociana": {
                    "sydney": {
                        "zones": ["1", "2", "3"]
                    },
                    "tokyo": {
                        "zones": ["1", "2", "3"]
                    },
                },
                "asia": {
                    "mumbai": {
                        "zones": ["1", "2", "3"]
                    },
                },
            },
        }
    },
    "gcp": {
        "pricing": {
            "internet": 0.09,
            "cross-region": 0.02,
            "cross-zone": 0.01,
        },
        "regions": {
            "us": {
                "east": {
                    "n.virginia": {
                        "zones": ["1", "2", "3"]
                    },
                },
                "west": {
                    "oregon": {
                        "zones": ["1", "2", "3"]
                    },
                },
            },
            "emea": {
                "europe": {
                    "frankfurt": {
                        "zones": ["1", "2", "3"]
                    },
                    "zurich": {
                        "zones": ["1", "2", "3"]
                    },
                },
            },
            "asia-pasific": {
                "ociana": {
                    "sydney": {
                        "zones": ["1", "2", "3"]
                    },
                    "tokyo": {
                        "zones": ["1", "2", "3"]
                    },
                },
                "asia": {
                    "mumbai": {
                        "zones": ["1", "2", "3"]
                    },
                },
            },
        }
    }
}
