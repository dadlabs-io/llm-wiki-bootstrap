# Using beacon

`beacon sync <folder>` uploads a folder to the object store.

Resuming is off by default: pass `--resume` to continue an interrupted upload. Without it, every run starts from scratch.

Every remote call goes through the single `send()` seam in `beacon/transport.py`, so the uploader can be tested with no network.
