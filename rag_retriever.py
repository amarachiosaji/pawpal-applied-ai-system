"""
rag_retriever.py

A lightweight retrieval component for PawPal+'s RAG feature.
Loads pet-care knowledge documents, chunks them into paragraphs,
and retrieves the most relevant chunks for a given query using TF-IDF
cosine similarity.
"""

import os
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RAGRetriever:
    """
    Retrieves relevant pet-care knowledge chunks for a given query.

    Attributes:
        knowledge_dir (str): Path to the folder containing .md knowledge files.
        chunks (list[dict]): Each dict has "source" (filename) and "text" (chunk content).
        vectorizer (TfidfVectorizer): Fitted TF-IDF vectorizer over all chunks.
        chunk_vectors: TF-IDF matrix representing all chunks.
    """

    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = knowledge_dir
        self.chunks = self._load_and_chunk_docs()

        if not self.chunks:
            raise ValueError(
                f"No knowledge chunks found in '{knowledge_dir}'. "
                "Make sure your .md files exist and contain paragraph text."
            )

        # Character n-grams handle plurals/tense variation (dog/dogs, walk/walking)
        # without needing a separate stemming library.
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        chunk_texts = [c["text"] for c in self.chunks]
        self.chunk_vectors = self.vectorizer.fit_transform(chunk_texts)

    def _load_and_chunk_docs(self) -> list[dict]:
        """
        Reads every .md file in knowledge_dir and splits it into paragraph-level
        chunks (split on blank lines). Skips very short chunks (e.g. headers alone).

        Returns:
            List of {"source": filename, "text": chunk_text} dicts.
        """
        chunks = []
        md_files = glob.glob(os.path.join(self.knowledge_dir, "*.md"))

        for filepath in md_files:
            filename = os.path.basename(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            raw_paragraphs = content.split("\n\n")

            for para in raw_paragraphs:
                cleaned = para.strip()
                if len(cleaned) < 40 or cleaned.startswith("#"):
                    continue
                chunks.append({"source": filename, "text": cleaned})

        return chunks

    def retrieve(self, query: str, top_k: int = 2, min_score: float = 0.10) -> list[dict]:        
        """
        Returns the top_k most relevant chunks for the query, provided their
        similarity score clears min_score. If nothing clears the threshold,
        returns an empty list rather than forcing a low-quality match.

        Args:
            query: Search string, e.g. "dog walking duration senior".
            top_k: Max number of chunks to return.
            min_score: Minimum cosine similarity required to include a result.

        Returns:
            List of {"source": str, "text": str, "score": float}, sorted by
            score descending. Empty list if no chunk clears min_score.
        """
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.chunk_vectors)[0]

        scored_chunks = [
            {
                "source": self.chunks[i]["source"],
                "text": self.chunks[i]["text"],
                "score": float(similarities[i]),
            }
            for i in range(len(self.chunks))
        ]
        scored_chunks.sort(key=lambda c: c["score"], reverse=True)

        results = [c for c in scored_chunks if c["score"] >= min_score]
        return results[:top_k]


if __name__ == "__main__":
    retriever = RAGRetriever(knowledge_dir="knowledge")

    test_queries = [
        "dog walking duration",
        "cat matting fur brushing",
        "medication missed dose",
        "asdkjqwe nonsense gibberish",
    ]

    for q in test_queries:
        print(f"\nQuery: '{q}'")
        results = retriever.retrieve(q)
        if not results:
            print("  No relevant guidance found.")
        else:
            for r in results:
                print(f"  [{r['source']}] (score={r['score']:.3f}) {r['text'][:80]}...")