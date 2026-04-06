---
description: Run the python test suite
---

# Run Tests

This workflow executes the `pytest` test suite for every isolated tool inside the `tools/` Monorepo directory.

// turbo
```bash
# Activate virtual environment
source .venv/bin/activate

# Iterate over all packages in the tools/ directory
for tool in tools/*/; do
  echo "=> Testing $tool"
  (cd "$tool" && pip install -e ".[dev]" && pytest tests/)
done
```
