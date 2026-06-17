import re
from rank_bm25 import BM25Okapi


def tokenize(text: str):
    return re.findall(r"\b\w+\b", text.lower())


class BM25Index:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.tokens = [tokenize(chunk["chunk_text"]) for chunk in chunks]
        self.index = BM25Okapi(self.tokens)

    def search(self, query: str, top_k: int = 30):
        scores = self.index.get_scores(tokenize(query))

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        return [
            {
                "rank": rank + 1,
                "score": float(score),
                "payload": self.chunks[idx]
            }
            for rank, (idx, score) in enumerate(ranked)
        ]