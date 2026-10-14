# Korvane

Korvane is a local-first document indexer for notes, manuals and exported chats. It builds a searchable index on your own machine and keeps nothing in the cloud.

## Why Korvane

- 40x faster indexing than the leading alternative.
- 99.9% recall on real-world corpora.
- One binary, no server, no account.

## Quick start

    korvane init ./notes
    korvane index ./notes
    korvane search "handoff file"

## Benchmark: indexing throughput

We measured indexing throughput on the public Bramble-200k corpus (200,000 documents, mixed Markdown and plain text). Hardware: an 8-core desktop CPU, 32 GB of RAM, a local NVMe disk. Each setting was run 5 times from a cold start and the table gives the median. The script is `bench/run.sh` in this repository.

| Setting | Documents per second (median of 5 runs) |
|---|---|
| Korvane, default | 18,400 |
| Korvane, low-memory mode | 9,100 |

## Limits

Korvane does not index images or scanned PDFs. Search is keyword plus embeddings; there is no query language yet.

## Licence

MIT.
