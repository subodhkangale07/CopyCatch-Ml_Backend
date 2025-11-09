import requests
import re
import string
import nltk
import tempfile
import os
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from PyPDF2 import PdfReader
import docx
from app.db import similarity_report_col
from app.db import documents_col
from app.makeShingles import get_shingles
from app.getShingleId import get_shingle_id
from app.makeMinHashSignature import minhash_signature
from app.makeBuckets import lsh_buckets
from app.getSimilarityScore import est_jaccard
from app.getMatchedContent import longest_common_chunks
import time

nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("omw-1.4")

def download_file(url):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        ext = os.path.splitext(url)[1]
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        for chunk in response.iter_content(chunk_size=8192):
            tmp_file.write(chunk)
        tmp_file.close()
        return tmp_file.name
    else:
        raise Exception(f"Error downloading file! Status code: {response.status_code}")


def extract_text_from_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_docx(path):
    doc = docx.Document(path)
    return "\n".join([para.text for para in doc.paragraphs])

def preprocess_text(text):
    text = text.lower()
    print("Lowercase text:", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    stop_words = set(stopwords.words("english"))
    words = [w for w in text.split() if w not in stop_words]
    lemmatizer = WordNetLemmatizer()
    lemmatized_words = [lemmatizer.lemmatize(w, pos="v") for w in words]
    print("Lemmatized text:", " ".join(lemmatized_words))
    return " ".join(lemmatized_words)

def extract_and_preprocess(url,assignment_id,submission_id):
    start=start = time.perf_counter()
    path = download_file(url)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        raw_text = extract_text_from_pdf(path)
        print("extracted text",raw_text)
    elif ext == ".docx":
        raw_text = extract_text_from_docx(path)
    else:
        raise Exception("Unsupported file type! Use PDF or DOCX.")
    
    end=time.perf_counter()
    print(f"Time taken to download and extract text: {end - start:.2f} seconds")
    print("downloaded")
    start=time.perf_counter()
    processed_text = preprocess_text(raw_text)
    end=time.perf_counter()
    print(f"Time taken to preprocess text: {end - start:.2f} seconds")
    print("preprocessed extracted text", processed_text)
    start=time.perf_counter()
    shingles=get_shingles(processed_text)
    # print("Shingles",shingles)
    shinglesToIds = get_shingle_id(shingles)
    # for shingle in shingles:
    #     id=get_shingle_id(shingle)
    #     shinglesToIds.append(id)
    #     # print("Shingle:",shingle," ID:",id)
    # print("3",processed_text )

    end=time.perf_counter()
    print(f"Time taken to generate shingles and IDs: {end - start:.2f} seconds")

    start=time.perf_counter()
    minhash_sign=minhash_signature(shingles,shinglesToIds)
    # print("MinHash Signature:",len(minhash_sign))
    end=time.perf_counter()
    print(f"Time taken to compute MinHash signature: {end - start:.2f} seconds")

    return {"raw_text": raw_text, "processed_text": processed_text, "minhash_signature": minhash_sign}

def save_to_db(file_url, submission_id ,assignment_id):
    """Extract, preprocess, and insert into MongoDB"""
    if documents_col is None:
        raise Exception("Database connection not available!")

    data = extract_and_preprocess(file_url,assignment_id,submission_id)
    data["submission_id"] = submission_id
    data["file_url"] = file_url
    inserted = documents_col.insert_one(data)
    
    start=time.perf_counter()

    candidatePairs=set()
    bands=100
    rows=200//bands
    lsh_buckets(data["minhash_signature"],bands,rows,assignment_id,submission_id,candidatePairs)
    print("Candidate Pairs:",candidatePairs)
    for pair in candidatePairs:
        submission_id1=pair[0]
        submission_id2=pair[1]
        score=est_jaccard(submission_id1,submission_id2)
        matched_chunks=longest_common_chunks(submission_id1,submission_id2)
        upsert_similarity(similarity_report_col, submission_id1, submission_id2, assignment_id, score, matched_chunks)
        upsert_similarity(similarity_report_col, submission_id2, submission_id1, assignment_id, score, matched_chunks)
    end=time.perf_counter()
    print(f"Time taken to process LSH and similarity for candidate pairs: {end - start:.2f} seconds")
    return str(inserted.inserted_id)





def upsert_similarity(similarity_report_col, submission_id1, submission_id2, assignment_id, score, matched_chunks):
    # 1. Try updating if the entry already exists in plagarized_with
    result = similarity_report_col.update_one(
        {
            "submission_id": submission_id1,
            "assignment_id": assignment_id,
            "plagarized_with.submission_id": submission_id2
        },
        {
            "$set": {
                "plagarized_with.$.similarity_score": score,
                "plagarized_with.$.matched_chunks": matched_chunks
            }
        }
    )

    # 2. If no match found, push a new object
    if result.matched_count == 0:
        similarity_report_col.update_one(
            {"submission_id": submission_id1, "assignment_id": assignment_id},
            {
                "$push": {
                    "plagarized_with": {
                        "submission_id": submission_id2,
                        "similarity_score": score,
                        "matched_chunks": matched_chunks
                    }
                }
            },
            upsert=True
        )