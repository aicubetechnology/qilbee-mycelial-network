# Git Repository Checklist

## ✅ Files to INCLUDE in Git

### Core Source Code
- ✅ `services/` - All microservice source code
- ✅ `sdk/` - Python SDK source code
- ✅ `tests/` - Test files (*.py)
- ✅ `scripts/` - Utility scripts
- ✅ `infra/` - Infrastructure configuration

### Configuration
- ✅ `docker-compose.yml` - Docker orchestration
- ✅ `Makefile` - Build automation
- ✅ `pytest.ini` - Test configuration
- ✅ `requirements.txt` files - Python dependencies
- ✅ `.env.example` - Template for environment variables

### Documentation (Source Only)
- ✅ `README.md` - Main project README
- ✅ `docs/*.md` - All markdown documentation
- ✅ `export_*.sh` - Export scripts (source code)

### Git Configuration
- ✅ `.gitignore` - This file!

---

## ❌ Files to EXCLUDE from Git (Already in .gitignore)

### Development Tools & Personal Config
- ❌ `.claude/` - Development tool configuration
- ❌ `.vscode/` - VS Code settings
- ❌ `.idea/` - JetBrains IDE settings
- ❌ `.DS_Store` - macOS metadata

### Python Build Artifacts
- ❌ `__pycache__/` - Python cache
- ❌ `*.pyc`, `*.pyo` - Compiled Python
- ❌ `venv/` - Virtual environment
- ❌ `*.egg-info/` - Package metadata
- ❌ `build/`, `dist/` - Build outputs

### Test Artifacts
- ❌ `.pytest_cache/` - Pytest cache
- ❌ `.coverage` - Coverage data
- ❌ `coverage.xml` - Coverage report
- ❌ `htmlcov/` - HTML coverage report
- ❌ `tests/results/*.json` - Test result JSON files

### Secrets & API Keys
- ❌ `.env` - Environment variables
- ❌ `**/sk-ant-*` - API key files
- ❌ `**/sk-*` - Any secret keys
- ❌ `*.key`, `*.pem` - Certificate files
- ❌ `secrets/` - Secrets directory

### Generated Documentation
- ❌ `*.docx` - Word exports (generated from .md)
- ❌ `*.pdf` - PDF exports (generated from .md)
- ❌ `RESEARCH_PAPER.html` - HTML export

### Temporary Files
- ❌ `*.tmp`, `*.temp` - Temporary files
- ❌ `~$*` - Word/Office temp files
- ❌ `*.log` - Log files
- ❌ `logs/` - Log directory

### Database Files
- ❌ `*.db`, `*.sqlite` - SQLite databases
- ❌ `*.sql` - SQL dumps

---

## 🔍 Files That Need Review

### Files with API Keys (MUST REMOVE before commit)
```bash
# Check for hardcoded API keys
grep -r "sk-ant-" tests/ --include="*.py"
```

**Found in**: `tests/e2e/test_live_agents.py:30`
```python
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "sk-ant-api03-...")
```

**Action Required**: Remove hardcoded fallback API key, use environment variable only:
```python
# ✅ Good - no hardcoded key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable required")
```

### Documentation Files Mentioning External Services
These files contain legitimate documentation about integration, OK to commit:
- `docs/SYNTHETIC_WORKER_*.md` - Integration guides
- `docs/CHAT_WEBSOCKET_INTEGRATION.md` - WebSocket integration
- `docs/FINAL_TEST_REPORT.md` - Test reports

**Action**: Review to ensure no API keys or sensitive credentials in examples

---

## 📝 Pre-Commit Checklist

Before running `git commit`, verify:

- [ ] No hardcoded API keys in code
  ```bash
  grep -r "sk-ant-" . --include="*.py" --exclude-dir=venv
  grep -r "sk-proj-" . --include="*.py" --exclude-dir=venv
  ```

- [ ] No `.env` files added
  ```bash
  git status | grep "\.env"
  ```

- [ ] No generated files (*.pyc, __pycache__)
  ```bash
  git status | grep -E "(\.pyc|__pycache__)"
  ```

- [ ] No IDE-specific files
  ```bash
  git status | grep -E "(\.vscode|\.idea|\.claude)"
  ```

- [ ] Only source .md files (not generated .docx/.pdf)
  ```bash
  git status | grep -E "\.(docx|pdf)$"
  ```

- [ ] Test results not included
  ```bash
  git status | grep "tests/results"
  ```

---

## 🚀 Git Workflow

### Initial Setup

```bash
# 1. Initialize repository
git init

# 2. Review what will be committed
git status

# 3. Check .gitignore is working
git status --ignored

# 4. Add all files (respecting .gitignore)
git add .

# 5. Verify staged files (should NOT include secrets, build artifacts, etc.)
git status

# 6. Create initial commit
git commit -m "Initial commit: Qilbee Mycelial Network microservices"
```

### Before Each Commit

```bash
# 1. Check for secrets
./scripts/check-secrets.sh  # Create this script

# 2. Run tests
pytest tests/

# 3. Check what's staged
git diff --cached

# 4. Commit with descriptive message
git commit -m "Add feature: knowledge broadcasting API"
```

---

## 🛡️ Security Best Practices

### Environment Variables

Create `.env.example` template (safe to commit):
```bash
# .env.example (commit this)
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
QMN_DATABASE_URL=postgresql://localhost/qmn
QMN_REDIS_URL=redis://localhost:6379
```

Actual `.env` file (DO NOT commit):
```bash
# .env (in .gitignore, never commit)
ANTHROPIC_API_KEY=sk-ant-api03-actual-key-here
OPENAI_API_KEY=sk-proj-actual-key-here
QMN_DATABASE_URL=postgresql://user:pass@prod-db/qmn
QMN_REDIS_URL=redis://:password@prod-redis:6379
```

### API Key Management

**Never**:
- ❌ Hardcode API keys in source code
- ❌ Commit `.env` files
- ❌ Include keys in test files
- ❌ Store keys in documentation

**Always**:
- ✅ Use environment variables
- ✅ Add `.env.example` template
- ✅ Document which env vars are required
- ✅ Use secrets management in production (AWS Secrets Manager, etc.)

---

## 📊 Current Repository Status

### Files Currently Present (Will be excluded by .gitignore)

```
❌ .claude/settings.local.json
❌ .coverage
❌ coverage.xml
❌ htmlcov/
❌ .DS_Store
❌ deploy/.DS_Store
❌ tests/.DS_Store
❌ ~$SEARCH_PAPER.docx
❌ __pycache__/ (multiple locations)
❌ venv/ (entire directory)
❌ tests/results/*.json (5 test result files)
```

### Clean Repository After .gitignore

When you run `git add .`, these will be ignored automatically.

Total excluded files: ~100+ files
Total to commit: ~50-60 source files

---

## 🔧 Useful Git Commands

### Check what will be committed
```bash
git status
```

### See ignored files
```bash
git status --ignored
```

### Verify no secrets in staged files
```bash
git diff --cached | grep -i "sk-ant\|sk-proj\|password\|secret"
```

### Unstage a file
```bash
git reset HEAD <file>
```

### Remove file from git but keep locally
```bash
git rm --cached <file>
```

---

## ✅ Ready to Commit Checklist

- [x] `.gitignore` created and comprehensive
- [ ] No hardcoded API keys in source (need to fix test_live_agents.py)
- [ ] All build artifacts excluded
- [ ] All secrets excluded
- [ ] Generated docs excluded (keep source .md)
- [ ] Test results excluded
- [ ] Virtual environment excluded

**Action Items Before First Commit**:
1. Remove hardcoded API key from `tests/e2e/test_live_agents.py:30`
2. Verify no other secrets: `grep -r "sk-" tests/ --include="*.py" --exclude-dir=venv`
3. Run pre-commit checks
4. Review `git status` output
5. Commit!

---

**Last Updated**: November 1, 2025
