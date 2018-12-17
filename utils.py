from collections import defaultdict
import csv
import pickle

def load_columns(filename):
    with open(filename) as f:
        columns = defaultdict(list)
        reader = csv.DictReader(f)
        for row in reader:
            for (k, v) in row.items():
                columns[k].append(v)
    return columns


def load_all(filename):
    with open(filename, "rb") as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break
