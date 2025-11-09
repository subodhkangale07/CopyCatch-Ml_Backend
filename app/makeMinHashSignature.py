from app.db import hash_funcs_col
from app.getShingleId import get_shingle_id

def minhash_signature(shingles,shinglesToIds):
    """Compute MinHash signature for a document using hash parameters from DB"""
    
    # Recreate hash functions from DB parameters
    hash_funcs = []
    for h in hash_funcs_col.find():
        # print("Hash function:", h)
        for params in h["funcs"]:
            a = params["a"]
            b = params["b"]
            p = params["p"]
            hash_funcs.append(lambda x, a=a, b=b, p=p: (a * x + b) % p)
    
    # Convert shingles to IDs once
    # print("Shingle IDs:", shinglesToIds)
    # print
    # Compute MinHash signature
    sig = []
    for h in hash_funcs:
        min_val = min(h(sid) for sid in shinglesToIds)
        # print("MMin Val ",min_val)
        sig.append(min_val)
    
    # print("MinHash Signature:", sig)
    return sig
