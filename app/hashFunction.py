import random
from app.db import hash_funcs_col

def make_hash_funcs(num_funcs=200):
    """Generate num_funcs hash functions of the form h(x) = (a*x + b) % p and store parameters in DB"""
    funcs_params = []
    p = 2 ** 31 - 1  # large prime
    for _ in range(num_funcs):
        a = random.randint(1, p - 1)
        b = random.randint(0, p - 1)
        funcs_params.append({"a": a, "b": b, "p": p})

    # Store in DB
    hash_funcs_col.insert_one({"num_funcs": num_funcs, "funcs": funcs_params})
 