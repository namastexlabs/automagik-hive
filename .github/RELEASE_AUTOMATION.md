# 🤖 Automated Release Workflow

Systematic, GitHub-native release automation using **Conventional Commits** and **Release Please**.

## 🎯 Goals

1. **Zero manual version bumping** - Automated from commit messages
2. **Automatic changelog generation** - From conventional commits
3. **PR-based releases** - Review before publishing
4. **Pre-release support** - RC, beta, alpha detection
5. **PyPI integration** - Automatic publishing on merge

## 📋 Workflow Overview

```
Commits → Release Please → Release PR → Merge → PyPI Publish
   ↓            ↓              ↓           ↓         ↓
  feat:    Analyzes      Creates PR   Merges    Publishes
  fix:     commits       w/ version   to main   to PyPI
  BREAKING: Bumps ver.   + changelog  Creates
                                      tag
```

## 🔄 The Flow

### 1. Developers Make Commits (Conventional Commits)

```bash
# Feature commit (minor version bump)
git commit -m "feat: add CORS configuration for agno.os integration"

# Fix commit (patch version bump)
git commit -m "fix: agent ID serialization in AgentOS API"

# Breaking change (major version bump)
git commit -m "feat!: redesign authentication system

BREAKING CHANGE: API authentication now requires OIDC tokens"

# Pre-release marker (creates RC)
git commit -m "feat: knowledge hot reload

Release-As: 0.2.0-rc.1"
```

### 2. Release Please Bot (Automated)

**On every push to `main` or `dev`:**
- Analyzes commit history since last release
- Determines version bump (major/minor/patch)
- Generates changelog from commits
- Creates/updates a **Release PR**

### 3. Release PR (Review Gate)

**Example PR created by bot:**
```
Title: chore(main): release 0.2.0

Changes:
- version: 0.1.1b2 → 0.2.0
- CHANGELOG.md: Generated from commits
- pyproject.toml: Version updated

Changelog:
### Features
* CORS configuration for agno.os integration (#52)
* Agent ID serialization corrections (#53)
* Knowledge hot reload functionality (#55)
```

**Developers review and approve** - No manual editing needed!

### 4. Merge → Auto Publish

**When Release PR is merged:**
- GitHub creates git tag automatically
- Triggers PyPI publishing workflow
- Package published within 5 minutes
- GitHub Release created with changelog

## 🛠️ Implementation

### Step 1: Add Release Please Workflow

Create `.github/workflows/release-please.yml`:

```yaml
name: Release Please

on:
  push:
    branches:
      - main
      - dev

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/release-please-action@v4
        with:
          release-type: python
          package-name: automagik-hive
          # Optional: Custom configuration
          config-file: .github/release-please-config.json
          manifest-file: .github/.release-please-manifest.json
```

### Step 2: Configure Release Please

Create `.github/release-please-config.json`:

```json
{
  "release-type": "python",
  "packages": {
    ".": {
      "package-name": "automagik-hive",
      "changelog-path": "CHANGELOG.md",
      "version-file": "pyproject.toml",
      "extra-files": [
        "pyproject.toml"
      ]
    }
  },
  "bump-minor-pre-major": true,
  "bump-patch-for-minor-pre-major": false,
  "prerelease": false,
  "draft": false,
  "changelog-sections": [
    {
      "type": "feat",
      "section": "Features"
    },
    {
      "type": "fix",
      "section": "Bug Fixes"
    },
    {
      "type": "perf",
      "section": "Performance Improvements"
    },
    {
      "type": "refactor",
      "section": "Code Refactoring"
    },
    {
      "type": "docs",
      "section": "Documentation"
    },
    {
      "type": "test",
      "section": "Tests"
    },
    {
      "type": "ci",
      "section": "CI/CD"
    }
  ]
}
```

### Step 3: Update PyPI Workflow

Modify `.github/workflows/publish-pypi.yml`:

```yaml
on:
  push:
    tags:
      - 'v*.*.*'
  release:
    types: [published]  # Add this - triggers on Release Please merge
```

### Step 4: Initial Manifest

Create `.github/.release-please-manifest.json`:

```json
{
  ".": "0.1.1b2"
}
```

## 🎨 Commit Convention

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- **feat**: New feature (minor bump)
- **fix**: Bug fix (patch bump)
- **docs**: Documentation only
- **style**: Code style (formatting)
- **refactor**: Code refactoring
- **perf**: Performance improvement
- **test**: Adding tests
- **ci**: CI/CD changes
- **chore**: Maintenance tasks

### Breaking Changes
```
feat!: new authentication system

BREAKING CHANGE: Old API tokens no longer supported
```
**Result**: Major version bump (0.x.x → 1.0.0)

### Pre-releases
```
feat: new feature

Release-As: 1.0.0-rc.1
```

## 🚀 Usage Examples

### Scenario 1: Regular Feature Development

```bash
# Developer workflow
git checkout -b feat/new-dashboard
# ... make changes ...
git commit -m "feat: add analytics dashboard"
git push origin feat/new-dashboard

# Create PR, get reviewed, merge to main
gh pr create --title "Add analytics dashboard" --body "..."

# When merged to main:
# → Release Please creates/updates Release PR
# → Shows version will bump: 0.2.0 → 0.3.0
# → Includes changelog entry

# Team lead reviews Release PR and merges
# → Tag v0.3.0 created automatically
# → PyPI publishing triggered
# → Package published in ~5 minutes
```

### Scenario 2: Pre-release (RC)

```bash
# Create RC from dev branch
git checkout dev
git commit -m "feat: experimental feature

Release-As: 0.3.0-rc.1"
git push origin dev

# Release Please creates Release PR for RC
# Merge → v0.3.0-rc.1 published to PyPI
# Marked as pre-release automatically
```

### Scenario 3: Hotfix

```bash
git checkout -b hotfix/critical-bug
git commit -m "fix: resolve authentication bypass

SECURITY: Patches CVE-2024-XXXX"
git push

# Merge to main
# → Release Please bumps patch: 0.2.0 → 0.2.1
# → Auto-publishes hotfix
```

## 🔐 Security & Control

### Protected Branches
```yaml
# .github/branch-protection.yml
main:
  required_reviews: 2
  require_codeowners: true
  required_status_checks:
    - ci-cd
    - security-scan
```

### Release Approval
- **Release PRs require approval** before merge
- **Team reviews** version bumps and changelogs
- **Manual control** over when releases happen
- **Rollback capability** by reverting Release PR

## 📊 Benefits

### For Developers
✅ No manual version bumping
✅ No changelog writing
✅ Clear commit message standards
✅ Automated documentation

### For Team Leads
✅ Review all changes before release
✅ Control release timing
✅ Automatic compliance documentation
✅ Full audit trail

### For DevOps
✅ Consistent release process
✅ Zero configuration drift
✅ Automatic semantic versioning
✅ Integration with existing CI/CD

## 🆚 Comparison: Manual vs Automated

| Step | Manual (Current) | Automated (Release Please) |
|------|------------------|----------------------------|
| Version bump | `make bump-rc` | Automatic from commits |
| Changelog | Manual writing | Auto-generated |
| Git tag | `make release-rc` | Auto-created on merge |
| PyPI publish | Manual trigger | Auto on tag push |
| Documentation | Manual update | Auto in Release PR |
| **Total time** | ~10 minutes | ~2 minutes (review only) |
| **Error rate** | Medium | Very low |
| **Consistency** | Variable | 100% consistent |

## 🎯 Migration Plan

### Phase 1: Setup (30 minutes)
1. Add Release Please workflow
2. Configure release-please-config.json
3. Create initial manifest
4. Test with dummy commit

### Phase 2: Team Training (1 hour)
1. Conventional Commits workshop
2. Create commit message templates
3. Setup git hooks for validation
4. Update CONTRIBUTING.md

### Phase 3: Pilot (1 week)
1. Run parallel with manual releases
2. Validate Release Please PRs
3. Gather team feedback
4. Adjust configuration

### Phase 4: Full Adoption (ongoing)
1. Disable manual release commands
2. Make Release Please primary workflow
3. Monitor and optimize

## 🔧 Optional Enhancements

### Git Commit Message Validation
```bash
# .git/hooks/commit-msg
#!/bin/sh
npx --yes @commitlint/cli --edit $1
```

### VS Code Extension
Install "Conventional Commits" extension for commit message assistance.

### Automated Release Notes
Release Please can pull PR descriptions into release notes automatically.

### Multi-Package Support
Can manage monorepo with multiple packages (future-proof).

## 📚 References

- [Release Please](https://github.com/googleapis/release-please)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

---

**Recommendation**: Adopt Release Please for systematic, low-maintenance release automation.
