
# from app.db import shingles_to_ids_col
# def get_shingle_id(shingle):
#     """Convert shingle (string) to a unique integer ID using a simple hash function"""
#     if shingles_to_ids_col.find_one({"shingle": shingle}):
#         return shingles_to_ids_col.find_one({"shingle": shingle})["id"]
#     max_id = shingles_to_ids_col.find_one(sort=[("id", -1)])
#     if(max_id is None):
#         max_id = 0
#     else:
#         max_id = max_id["id"]
#     new_id = max_id+1 # Modulo to keep IDs manageable in size
#     shingles_to_ids_col.insert_one({"shingle": shingle, "id": new_id})
#     return new_id




from app.db import shingles_to_ids_col

def get_shingle_id(shingles):
    """
    Convert an array of shingles to unique IDs.
    - Loads existing shingle->id mapping from DB once.
    - Assigns new IDs for shingles not present.
    - Updates DB in a single insert_many call.
    Returns a list of IDs corresponding to input shingles.
    """
    # Step 1: Load existing shingle->id mapping from DB
    existing_shingles = list(shingles_to_ids_col.find({}, {"_id": 0, "shingle": 1, "id": 1}))
    
    # Step 2: Build dictionary for fast lookup
    shingle_to_id = {}
    max_id = 0  # default starting ID if collection is empty
    for item in existing_shingles:
        shingle_to_id[item["shingle"]] = item["id"]
        if item["id"] > max_id:
            max_id = item["id"]

    # Step 3: Prepare IDs for input shingles
    ids = []
    new_entries = []

    for shingle in shingles:
        if shingle in shingle_to_id:
            # Already exists, reuse ID
            ids.append(shingle_to_id[shingle])
        else:
            # New shingle, assign next ID
            max_id += 1
            shingle_to_id[shingle] = max_id
            ids.append(max_id)
            new_entries.append({"shingle": shingle, "id": max_id})

    # Step 4: Insert new entries in DB in one go
    if new_entries:
        shingles_to_ids_col.insert_many(new_entries)

    return ids