from pymongo import MongoClient

client = MongoClient("mongodb+srv://subodhkangale_db_user:qCJOcWZe0VLABGSV@cluster0.xaomrca.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["test"]

# Check if "PreProcessing" collection exists, otherwise create it
if "PreProcessing" not in db.list_collection_names():
    db.create_collection("PreProcessing")

documents_col = db["PreProcessing"]

if "HashFunctions" not in db.list_collection_names():
    db.create_collection("HashFunctions")

hash_funcs_col = db["HashFunctions"]

if "ShinglesToIds" not in db.list_collection_names():
    db.create_collection("ShinglesToIds")
shingles_to_ids_col = db["ShinglesToIds"]

if "Buckets" not in db.list_collection_names():
    db.create_collection("Buckets")

buckets_col = db["Buckets"]

if "SimilarityReport" not in db.list_collection_names():
    db.create_collection("SimilarityReport")

similarity_report_col = db["SimilarityReport"]