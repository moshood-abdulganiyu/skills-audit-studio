### Step 1: Repo and layout
- Pattern: decide the folder layout and environment before writing code; pin the Python version and commit the lock file.
- Commands that mattered: uv init --bare, uv python pin 3.12, uv venv, git status before every commit, git branch -M main
- Mistake or surprise: a stray "Untitled" file from the editor was committed because git add . stages everything. Reading git status first catches it.
- Next time: save or close unnamed editor files before git add, and check notebook size or outputs before committing.