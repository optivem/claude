Update the MIGRATION.md plan based on corrections and decisions made during this conversation.

Steps:

1. Review the conversation history for any corrections the user gave (e.g. "no not that", "actually do X instead", "don't do Y") and decisions that changed the approach.

2. Read the current MIGRATION.md in the starter repo:
```bash
cat "$(git rev-parse --show-toplevel)/../starter/MIGRATION.md"
```

3. For each correction or decision found:
   - Identify which section of MIGRATION.md it relates to
   - Update that section with the new approach, adding inline notes where relevant
   - If no section exists, add one

4. Show the user a summary of what was updated and why.

Do NOT add raw conversation text — distill corrections into clear, actionable plan updates.
