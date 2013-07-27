
from os.path import join

DATA_DIR = "/home/chase.kernan/data/seis-gcm/"

def make_data_path(name):
    return join(DATA_DIR, name)


def make_dtype(**fields):
    return fields.items()