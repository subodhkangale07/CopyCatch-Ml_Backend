

def get_shingles(text, k=2):
    """Return set of k-word shingles from text"""
    words = text.split()
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}
