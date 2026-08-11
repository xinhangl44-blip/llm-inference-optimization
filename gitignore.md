# Gitignore Configuration

This document contains the `.gitignore` rules for the project.

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/

# Environment
.env
*.env

# Secrets (never commit)
*secret*.yaml
*-secret.yaml

# Logs
*.log
logs/

# Large files
*.tar
*.tar.gz
*.zip

# Model cache
*.cache/
huggingface/

# Temporary files
XADD
XLEN
test.py

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```
