---
description: Commit all changes and push to GitHub
---

# Save & Push to GitHub

// turbo-all

1. Stage all changes:

```powershell
git -C "c:\Users\lvqua\.gemini\antigravity\scratch\personal-finance" add -A
```

1. Check if there are changes to commit:

```powershell
git -C "c:\Users\lvqua\.gemini\antigravity\scratch\personal-finance" status --porcelain
```

If there are no changes, inform the user "Nothing to commit — already up to date." and stop.

1. Commit with a descriptive message summarising what changed (look at staged diff to determine the message):

```powershell
git -C "c:\Users\lvqua\.gemini\antigravity\scratch\personal-finance" commit -m "<descriptive message>"
```

1. Push to GitHub:

```powershell
git -C "c:\Users\lvqua\.gemini\antigravity\scratch\personal-finance" push
```

1. Confirm to the user that changes have been saved and pushed, and include the commit hash from the output.
