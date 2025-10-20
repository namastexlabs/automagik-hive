# 🎯 Controlled Release Workflow

**Simple principle**: **YOU decide the version**, workflow handles the mechanics.

## 🚀 How to Release

### Step 1: Decide the Version

You control semantic versioning:

- **Minor** (0.2.0 → 0.3.0): New features, enhancements
- **Patch** (0.2.0 → 0.2.1): Bug fixes, small changes
- **Pre-release** (0.2.0-rc.1): Release candidates for testing

### Step 2: Trigger Release Workflow

1. **Go to GitHub Actions**:
   - https://github.com/namastexlabs/automagik-hive/actions/workflows/create-release.yml

2. **Click "Run workflow"**:
   - **Version**: Enter version (e.g., `0.2.0` or `0.2.0-rc.1`)
   - **Pre-release**: Check if this is RC/beta
   - **Branch**: Select `dev` or `main`
   - Click "Run workflow"

3. **Wait ~30 seconds**:
   - Workflow updates `pyproject.toml`
   - Generates changelog from git commits
   - Creates Release PR automatically

4. **Review & Merge**:
   - Check the Release PR
   - Verify version and changelog
   - Merge → PyPI publishes automatically

## 📊 Example: Releasing v0.2.0

```
Scenario:
- Last release: v0.1.1b2
- Current commits on dev:
  - feat: CORS configuration
  - fix: agent ID serialization
  - feat: knowledge hot reload
- Decision: This is a minor release → v0.2.0

Steps:
1. Go to Actions → Create Release workflow
2. Enter version: 0.2.0
3. Pre-release: false (unchecked)
4. Branch: dev
5. Run workflow

Result:
- PR created: "🚀 Release: v0.2.0"
- Version bumped in pyproject.toml
- Changelog lists all commits since v0.1.1b2
- Review & merge → Published to PyPI
```

## 📋 Version Decision Guide

### When to bump Minor (0.x.0)
✅ New features added
✅ Significant enhancements
✅ Breaking changes (before 1.0.0)
✅ Multiple features bundled together

**Example**: v0.2.0 (CORS + agent ID + knowledge reload)

### When to bump Patch (0.0.x)
✅ Bug fixes only
✅ Small improvements
✅ Documentation updates
✅ Performance tweaks

**Example**: v0.2.1 (hotfix for CORS issue)

### When to use Pre-release (0.x.0-rc.N)
✅ Testing before stable release
✅ Beta features for early adopters
✅ Release candidates

**Example**: v0.3.0-rc.1 (testing new dashboard)

## 🔄 Typical Release Cadence

### Weekly/Bi-weekly (Patches)
```
Monday:    v0.2.1 (bug fixes from last week)
Friday:    v0.2.2 (performance improvements)
```

### Monthly (Minor)
```
End of month: v0.3.0 (all features from the month)
```

### As Needed (Pre-releases)
```
Before major release: v1.0.0-rc.1, v1.0.0-rc.2
```

## 🎨 What the Workflow Does

**Automatically:**
- ✅ Updates version in `pyproject.toml`
- ✅ Generates changelog from commits
- ✅ Creates release branch
- ✅ Creates Release PR with all details
- ✅ Adds proper co-author attribution

**You control:**
- 🎯 Version number
- 🎯 When to release
- 🎯 What goes in each release
- 🎯 Review before publishing

## 🆚 Comparison

| Aspect | Old Manual | New Workflow |
|--------|-----------|--------------|
| Version decision | You decide | **You decide** |
| Version bump | `make bump-rc` | Workflow does it |
| Changelog | Manual writing | Auto-generated |
| Git operations | `make release-rc` | Workflow handles |
| PyPI publish | Triggered by tag | Auto on PR merge |
| **Control** | **Full** | **Full** |
| **Automation** | Partial | Full |

## 🔍 Generated Changelog Example

When you trigger release for v0.2.0, the workflow generates:

```markdown
## Changes in v0.2.0

- feat: CORS configuration for agno.os integration (be387b9)
- fix: agent ID serialization in AgentOS API (8927a29)
- feat: knowledge hot reload functionality (f121348)
- Merge pull request #52 from namastexlabs/fix/cors-agno-os-integration (cd6180a)
- Merge pull request #53 from namastexlabs/fix/agent-id-serialization (083d069)
- Merge pull request #55 from namastexlabs/hotfix/knowledge-hot-reload (50d33a9)

---
Generated from commits since last release
```

## 🎯 Benefits

### For Team Leads
✅ **Full control** over version numbers
✅ **Decide when** to release (not automated)
✅ **Review everything** before publishing
✅ **Batch features** as makes sense

### For Developers
✅ **No workflow changes** - commit as usual
✅ **No manual versioning** - workflow handles it
✅ **Automatic changelogs** - from git history
✅ **Fast releases** - 5 minutes total

### For DevOps
✅ **Consistent process** every time
✅ **Audit trail** via GitHub PRs
✅ **Rollback capable** - just revert PR
✅ **No credentials needed** - trusted publishing

## 🆘 Common Scenarios

### "We need a hotfix NOW"
```
1. Fix merged to main
2. Run workflow: version = 0.2.1
3. Merge Release PR
4. Published in 5 minutes
```

### "Let's bundle this month's features"
```
1. Multiple features merged to dev over 2 weeks
2. Run workflow: version = 0.3.0
3. Review all changes in Release PR
4. Merge → Published
```

### "We want to test before stable release"
```
1. Run workflow: version = 0.3.0-rc.1, pre-release = true
2. Merge Release PR
3. Test with: pip install automagik-hive==0.3.0-rc.1
4. If good: Run workflow again with version = 0.3.0
```

## 🚦 Migration from Make Commands

### Current (Still Works)
```bash
make bump-rc    # Manual version bump
make release-rc # Manual git operations
```

### New (Recommended)
```
GitHub Actions → Create Release workflow
- Enter version
- Click button
- Review PR
- Merge
```

**Both methods work!** Use whichever fits the situation.

## 📚 FAQ

**Q: Can I still use semantic commit messages?**
A: Yes! They help generate better changelogs.

**Q: What if the changelog is wrong?**
A: Edit the Release PR description before merging.

**Q: Can I skip the PR and go direct to PyPI?**
A: No - the PR is the review gate. Always required.

**Q: What if I enter the wrong version?**
A: Close the Release PR and run workflow again with correct version.

**Q: Do I need to follow semantic versioning strictly?**
A: No - you decide the version. The format just needs to be X.Y.Z[-suffix].

---

**TL;DR**: Click button → Enter version YOU choose → Review PR → Merge → Published. Simple as that.
