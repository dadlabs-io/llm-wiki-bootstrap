# Retrieval versus long context — notes from a team trial

Written for the skill test fixtures, September 2026.

Our assistant answers questions about an internal handbook of about 300 pages. We tried two ways of giving the model what it needs.

**Long context.** Put the whole handbook in the prompt every time. Answers were good, but every question paid for the full handbook, and answers slowed as the handbook grew.

**Retrieval.** Split the handbook into sections, search them for each question, and put only the top matches in the prompt. The prompt shrank by roughly 40%, and in a check of 20 known questions, 18 were answered correctly, the same count as long context. The two misses were questions whose answer was spread over several sections the search did not rank together.

What we took from it:
- Retrieval wins on cost once the source is large and questions are narrow.
- Long context is the safer choice when an answer depends on many parts of the source at once.
- Whatever you choose, keep a small set of known questions and re-run it when the source or the model changes.
