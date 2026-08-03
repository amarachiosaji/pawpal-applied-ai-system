"""Temporary diagnostic: show ALL candidate scores per query, not just the winner."""

from rag_retriever import RAGRetriever

retriever = RAGRetriever(knowledge_dir="knowledge")

test_queries = [
    "Feed & fresh water Feeding Cat",
    "Vet appointment Health Dog",
    "Dinner Feeding Dog",
    "Litter box cleaning Hygiene Cat",
    "Grooming Hygiene Cat",
]

for q in test_queries:
    print(f"\n{'=' * 50}\nQuery: '{q}'")
    query_vector = retriever.vectorizer.transform([q])
    from sklearn.metrics.pairwise import cosine_similarity
    sims = cosine_similarity(query_vector, retriever.chunk_vectors)[0]
    scored = sorted(
        [(retriever.chunks[i]["source"], sims[i], retriever.chunks[i]["text"][:60]) for i in range(len(sims))],
        key=lambda x: x[1],
        reverse=True,
    )
    for source, score, snippet in scored[:5]:
        print(f"  {score:.3f}  [{source}]  {snippet}...")