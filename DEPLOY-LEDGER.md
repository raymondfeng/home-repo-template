# Deploy ledger

One entry per deploy, newest first. `scripts/deploy.sh` reads the top entry: its deploy id is the Worker version that
must still be the one serving, and its HEAD is the baseline for the next delta. So the words
"at deploy" and "HEAD" in an entry, each followed by its value in backticks, are a format the script depends on.

Keep the story here and the rule in `.agents/skills/deploy-site/RULES.md`: when a deploy earns a rule, add the rule
there and the incident to the entry.

Format for a new entry (prepend it above the newest one):

> **N files** (measured **YYYY-MM-DD** at deploy `version id`, HEAD `sha`: *a one-line title*).
> Baseline: the previous deploy's version id. Delta: **+a added / −r removed**, each added file named.
> Protection: 302 on k of k paths of the site's address. Live probes: k of k, with what each one checked.
> **Lesson:** what this deploy taught, if anything.

<!-- entries start below this line -->
