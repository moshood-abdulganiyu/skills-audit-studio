### Step 1: Repo and layout
- Pattern: Decide the folder structure and pin the environment before writing code.
- Commands that mattered: git clone, uv python pin, uv sync, git status before every commit
- Mistake or surprise: Cloning the GitHub repo (instead of git init + push) avoids a rejected first push when GitHub creates the LICENSE. Setuptools can't auto-discover a flat layout with several top-level folders, so build config waits until core/ exists.
- Next time: Write .gitignore first and check git status before the first commit.