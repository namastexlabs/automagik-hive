# QUICK ACTION GUIDE - Directory Cleanup

**Created**: 2025-10-29  
**Full Report**: `DIRECTORY_AUDIT_REPORT.md`

---

## IMMEDIATE ACTIONS (This Week)

### Action 1: Move common/ → lib/services/

Currently the `common/` directory at project root contains notification utilities.  
These should be moved to `lib/services/` where other service modules live.

**Steps**:
```bash
# 1. Move directory
mv common/ lib/services/notifications

# 2. Update imports in api/serve.py
#    Change: from common.startup_notifications import ...
#    To:     from lib.services.notifications.startup_notifications import ...

# 3. Move tests
mv tests/common/ tests/lib/services/notifications

# 4. Update test imports similarly

# 5. Commit
git add .
git commit -m "chore: reorganize notification system into lib/services"
```

**Impact**: 2 files change (api/serve.py imports)  
**Testing**: Run `pytest tests/lib/services/notifications/`  
**Risk**: LOW - Isolated change

---

### Action 2: Delete logs/ directory

The `logs/` directory is empty and serves no purpose.

**Steps**:
```bash
# 1. Verify it's empty
ls -la logs/

# 2. Delete
git rm -r logs/

# 3. Commit
git commit -m "chore: remove empty logs directory"
```

**Impact**: Zero - directory is unused  
**Risk**: NONE - can be recreated if needed  
**Time**: 5 minutes

---

## INVESTIGATION REQUIRED (Next Sprint)

### Question 1: Is genie/ actively used?

The `genie/` directory contains execution reports and wish documents.  
**Check if** this is being actively used by Automagik Forge or if it's legacy.

```bash
# Check for references
grep -r "genie/" . --include="*.py" --exclude-dir=.venv | grep -v ".pyc"

# Check .gitignore
grep "genie" .gitignore

# Check git logs for recent activity
git log --oneline --all -- genie/ | head -20
```

**Possible outcomes**:
- A) ACTIVE wish system → Keep, document in CLAUDE.md
- B) LEGACY reports → Archive to docs/archive/
- C) EXTERNAL system → Ignore, add to .gitignore

---

### Question 2: Which scripts are actually used?

The `scripts/` directory has 19 files but unclear which are active.

**Steps to audit**:
```bash
# 1. Check GitHub Actions references
grep -r "scripts/" .github/workflows/ | grep -v node_modules

# 2. Check Makefile references
grep "scripts/" Makefile

# 3. Check code references
grep -r "scripts/" lib/ api/ ai/ --include="*.py" | grep -v ".pyc"

# 4. For each unclear script, check modification date
ls -lh scripts/*.py | sort -k6
```

**Result**: Categorize each script as:
- ACTIVE (used by CI/CD or startup)
- LEGACY (old, potentially unused)
- UNCLEAR (needs investigation)

---

## DIRECTORY STATISTICS

Current state:
```
common/       64 KB   → Move to lib/services/
logs/          4 KB   → Delete
genie/       484 KB   → Audit then decide
scripts/     232 KB   → Document and clean

lib/        2.6 MB   → Well-organized, no action
api/        256 KB   → Clean, no action
ai/         2.4 MB   → Properly modularized, no action
tests/      1.2 MB   → Mirrors source, no action
```

---

## SUCCESS CRITERIA

### After Action 1 (Move common/):
- [ ] `common/` directory no longer exists
- [ ] `lib/services/notifications/` contains notification files
- [ ] All imports in `api/serve.py` updated
- [ ] Tests run and pass: `pytest tests/lib/services/notifications/`
- [ ] No import errors on server startup

### After Action 2 (Delete logs/):
- [ ] `logs/` directory removed from repo
- [ ] Git history updated with removal commit
- [ ] No references to logs/ directory in code

### After Investigation (genie/):
- [ ] Decision documented: keep/archive/delete
- [ ] If keeping: documented in CLAUDE.md
- [ ] If archiving: moved to docs/archive/
- [ ] .gitignore updated if needed

### After Investigation (scripts/):
- [ ] `scripts/README.md` created
- [ ] Each script marked as ACTIVE/LEGACY/DEPRECATED
- [ ] Obsolete scripts removed
- [ ] CI/CD still works correctly

---

## RISK ASSESSMENT

**Low Risk**:
- Moving common/ (only 2 imports to update)
- Deleting logs/ (unused, empty)

**Medium Risk**:
- Removing scripts/ (need to verify CI/CD still works)

**Unknown Risk**:
- genie/ (depends on whether it's actively used)

---

## NEXT STEPS

1. **This week**: Complete Actions 1 & 2 (total 1-2 hours)
2. **Next sprint**: Investigation on genie/ and scripts/
3. **Following sprint**: Implementation of cleanup decisions

---

## NOTES

- Full analysis in `DIRECTORY_AUDIT_REPORT.md`
- All recommendations are non-breaking if done carefully
- Test suite should be run after each action
- Consider impact on team workflows before implementing
- Keep this guide handy for reference during implementation

