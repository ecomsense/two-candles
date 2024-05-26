from omspy_brokers.angel_one import AngelOne


def login(config):
    api = AngelOne(**config)
    if api.authenticate():
        print("api connected")
    else:
        print("api not connected")
    return api
