from app.db import buckets_col

def lsh_buckets(sig, bands, rows, assignment_id, submission_id, candidate_pairs):
    """
    Apply LSH to a single document's signature and update buckets and candidate pairs.

    sig: list[int]          -> MinHash signature of current submission
    bands: int              -> Number of bands
    rows: int               -> Number of rows per band (bands * rows = signature length)
    assignment_id: str/int  -> Assignment identifier
    submission_id: str/int  -> Current submission's ID
    candidate_pairs: set[tuple] -> Set of unique candidate pairs {(id1, id2), ...}
    """

    # Fetch existing assignment buckets from DB
    assignment_bucket = buckets_col.find_one({"assignment_id": assignment_id})
    
    # If no bucket exists for this assignment, create it
    if assignment_bucket is None:
        assignment_bucket = {
            "assignment_id": assignment_id,
            "buckets": []  # List of dicts: {"hash_val": int, "submission_ids": []}
        }
        buckets_col.insert_one(assignment_bucket)
    
    # Make sure to work with local copy for easier update
    buckets = assignment_bucket.get("buckets", [])

    for b in range(bands):
        start = b * rows
        end = start + rows
        band_tuple = tuple(sig[start:end])  # freeze band for hashing
        h = hash(band_tuple)

        # Find if this hash already exists in any bucket
        bucket_found = None
        for bucket in buckets:
            if bucket["hash_val"] == h:
                bucket_found = bucket
                break

        if bucket_found:
            # Update candidate pairs with current submission
            for existing_id in bucket_found["submission_ids"]:
                if existing_id != submission_id:  # skip self-pair
                    pair = tuple(sorted((existing_id, submission_id)))
                    candidate_pairs.add(pair)

            # Add current submission to the bucket if not already present
            if submission_id not in bucket_found["submission_ids"]:
                bucket_found["submission_ids"].append(submission_id)

        else:
            # Create new bucket for this hash
            new_bucket = {
                "hash_val": h,
                "submission_ids": [submission_id]
            }
            buckets.append(new_bucket)

    # Update buckets in MongoDB
    buckets_col.update_one(
        {"assignment_id": assignment_id},
        {"$set": {"buckets": buckets}}
    )

    return candidate_pairs, buckets
