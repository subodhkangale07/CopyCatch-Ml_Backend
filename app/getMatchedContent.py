from app.db import documents_col
import difflib

def longest_common_chunks(submission_id1, submission_id2, min_len: int = 10):
    """
    Extract maximal (longest) common substrings between doc1 and doc2.
    Only substrings of length >= min_len are kept.
    Removes overlapping duplicates, keeping longest match.
    """
    doc1_doc = documents_col.find_one({"submission_id": submission_id1})
    doc2_doc = documents_col.find_one({"submission_id": submission_id2})

    if doc1_doc is None or doc2_doc is None:
        raise ValueError("One or both submission IDs not found in database.")

    doc1 = doc1_doc.get("raw_text", "")
    doc2 = doc2_doc.get("raw_text", "")

    # Use difflib to find matching blocks
    matcher = difflib.SequenceMatcher(None, doc1, doc2)
    matching_blocks = matcher.get_matching_blocks()
    
    # Extract common substrings that meet minimum length
    common_chunks = []
    for match in matching_blocks:
        a, b, size = match
        if size >= min_len:
            substring = doc1[a:a + size]
            common_chunks.append((a, a + size, size, substring))
    
    # Sort by position in doc1
    common_chunks.sort(key=lambda x: x[0])
    
    # Remove overlapping chunks
    results = []
    last_end = 0
    
    for start, end, size, substring in common_chunks:
        if start >= last_end:
            results.append(substring)
            last_end = end
        else:
            # Overlap detected, keep the longer one
            prev_size = last_end - start
            if size > prev_size:
                if results:
                    results.pop()
                results.append(substring)
                last_end = end
    # print("results is here", results)
    return results