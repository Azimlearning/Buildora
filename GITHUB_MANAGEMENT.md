# GitHub Management Guide

**MANDATORY READING FOR ALL TEAM MEMBERS**

This document defines the strict Git workflow for the Buildora project. All team members MUST follow these rules.

---

## Branch Structure

### Protected Branches
- **`main`** - Production-ready code only. Direct pushes are FORBIDDEN.
- **`develop`** - Integration branch for completed features. Merge only via PR.

### Feature Branches
All work MUST happen in feature branches following this naming convention:

```
<owner>/<feature-name>
```

**Examples:**
- `azim/orchestrator-setup`
- `farah/upload-component`
- `khair/redis-client`
- `harry/agent-c-compliance`
- `ali/agent-c-logic`

---

## Workflow Rules

### 1. Starting New Work

```bash
# Always start from latest main
git checkout main
git pull origin main

# Create your feature branch
git checkout -b <your-name>/<feature-name>
```

### 2. Daily Work Cycle

```bash
# Make your changes
git add <specific-files>  # NEVER use 'git add .'
git commit -m "Clear description of what changed"

# Push to your branch
git push origin <your-name>/<feature-name>
```

### 3. Keeping Your Branch Updated

```bash
# Sync with main regularly (at least daily)
git checkout main
git pull origin main
git checkout <your-name>/<feature-name>
git merge main

# Resolve any conflicts, then push
git push origin <your-name>/<feature-name>
```

### 4. Creating Pull Requests

When your feature is complete:

1. **Push your latest changes**
2. **Go to GitHub** → https://github.com/Azimlearning/Buildora
3. **Click "New Pull Request"**
4. **Set:**
   - Base: `main`
   - Compare: `<your-name>/<feature-name>`
5. **Title format:** `[Component] Brief description`
   - Example: `[Orchestrator] Add LangGraph agent chain`
6. **Description must include:**
   - What changed
   - Why it changed
   - How to test it
   - Related files/components
7. **Request reviewers:** At least 1 other team member
8. **Link related issues** if any

### 5. Code Review Process

**As a PR Author:**
- Respond to all comments
- Make requested changes in new commits
- Re-request review after changes
- DO NOT merge your own PR

**As a Reviewer:**
- Review within 24 hours
- Check code quality, logic, and adherence to FILE_STRUCTURE.md
- Test locally if possible
- Approve only when satisfied

**Merge Requirements:**
- ✅ At least 1 approval
- ✅ All CI checks pass (when set up)
- ✅ No merge conflicts
- ✅ Up to date with main

---

## Component Ownership

| Component | Owner | Branch Prefix |
|-----------|-------|---------------|
| FastAPI Backend + Orchestrator | Chip/Azim | `azim/` |
| Agent A (Doc Reader) | Chip/Azim | `azim/` |
| Agent B (Monitor) | Khair | `khair/` |
| Agent C (Permits) | Harry + Aliasya | `harry/` or `ali/` |
| Agent D (Reports) | Farah | `farah/` |
| React Frontend | Farah | `farah/` |
| PostgreSQL + Redis | Khair | `khair/` |
| Infrastructure (Docker) | Chip/Azim | `azim/` |

---

## Commit Message Guidelines

### Format
```
[Component] Action: Brief description

Optional longer explanation if needed.
```

### Examples
✅ **GOOD:**
```
[Orchestrator] Add: LangGraph state machine for 4-agent pipeline
[Agent A] Fix: PDF parsing error on scanned documents
[Frontend] Update: Upload component with drag-and-drop
[Redis] Refactor: Connection pooling for better performance
```

❌ **BAD:**
```
fixed stuff
WIP
update
asdfasdf
```

---

## DO NOT

❌ **NEVER** commit directly to `main`
❌ **NEVER** force push (`git push -f`) to shared branches
❌ **NEVER** commit sensitive data (.env files, API keys)
❌ **NEVER** commit large binary files (use MinIO/external storage)
❌ **NEVER** merge your own PR without review
❌ **NEVER** use `git add .` (be explicit about what you're committing)

---

## Emergency Procedures

### Accidentally Committed to Main
```bash
# DO NOT PANIC
# Contact Chip/Azim immediately
# We'll help you revert safely
```

### Merge Conflict Help
```bash
# 1. Update your branch
git checkout main
git pull origin main
git checkout <your-branch>
git merge main

# 2. Git will mark conflicts in files
# 3. Open conflicted files and resolve manually
# 4. After resolving:
git add <resolved-files>
git commit -m "[Merge] Resolve conflicts with main"
git push origin <your-branch>
```

### Lost Work / Need to Undo
```bash
# See recent commits
git log --oneline

# Undo last commit (keeps changes)
git reset --soft HEAD~1

# Discard all local changes (DANGEROUS)
git reset --hard HEAD
```

---

## Quick Reference

```bash
# Check current branch and status
git status

# See all branches
git branch -a

# Switch branches
git checkout <branch-name>

# See commit history
git log --oneline --graph --all

# See what changed
git diff

# Stash changes temporarily
git stash
git stash pop
```

---

## Questions?

- **Git issues:** Ask Chip/Azim
- **PR process:** Ask anyone who's done one
- **Merge conflicts:** Pair with someone to resolve

**Remember:** It's better to ask than to break main! 🚀
