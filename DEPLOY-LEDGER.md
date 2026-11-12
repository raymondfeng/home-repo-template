# Deploy ledger

One entry per deploy, newest first. `scripts/deploy.sh` reads the top entry: its deploy hash is the deployment that
must still be the newest in production, and its HEAD is the baseline for the next delta. So the words
"at deploy" and "HEAD" in an entry, each followed by its value in backticks, are a format the script depends on.

Keep the story here and the rule in `.claude/skills/deploy-site/RULES.md`: when a deploy earns a rule, add the rule
there and the incident to the entry.

Format for a new entry (prepend it above the newest one):

> **N files** (measured **YYYY-MM-DD** at deploy `hash`, HEAD `sha`: *a one-line title*).
> Baseline: the previous deploy's hash. Delta: **+a added / −r removed**, each added file named.
> The new deployment's host: 302 on k of k paths. Live probes: k of k, with what each one checked.
> **Lesson:** what this deploy taught, if anything.

<!-- entries start below this line -->
