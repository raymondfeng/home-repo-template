# docs

The corpus. `CLAUDE.md` ("Where a doc goes") says which folder a new doc belongs in. Nothing sits at the top of this
folder except this file.

`landscape/example-source-read-2026-01-01.md` and `assets/example-source-2026-01-01/` are a worked example of a read
and its archive. The quote check runs over them (`python3 -I scripts/check-quotes.py --all`). Delete both, and their
entry in `scripts/quote-reads.json`, when you have a real read.
