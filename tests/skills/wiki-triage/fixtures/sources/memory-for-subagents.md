# Giving subagents a shared memory store

An orchestrator's subagents lose what each other learned. This piece adds a shared memory: every subagent writes short notes to a vector store, and the orchestrator retrieves the relevant notes into each new subagent's brief. Half of it is about the harness and delegation, half about the memory store and its retrieval.
