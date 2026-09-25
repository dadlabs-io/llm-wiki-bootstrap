# Tuning a vector index for an agent's long-term memory

Notes from a team that stores an assistant's memories as embeddings. They compare HNSW and IVF indexes for recall at a fixed latency, explain why they re-embed old memories when the embedding model changes, and describe a retrieval step that mixes keyword and vector search before a reranker picks what goes back into the context window.
