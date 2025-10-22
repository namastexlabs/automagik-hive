# Release Notes Template

This template is used by `.github/workflows/publish-pypi.yml` to generate release notes automatically.

## How to Customize

Edit this file to change the default release notes structure. The workflow will:
1. Use `generate_release_notes: true` to create automatic changelog from commits
2. Append this template content below the auto-generated changelog

## Template Variables

The following variables are available and will be replaced by the workflow:
- `{{VERSION}}` - The release version (e.g., 0.2.0rc2)
- `{{REPOSITORY}}` - The GitHub repository (e.g., namastexlabs/automagik-hive)

---

## Default Template

```markdown
## 📦 PyPI Release {{VERSION}}

This release has been published to PyPI and is ready for installation and testing.

### 🚀 Installation

\```bash
# Install from PyPI
pip install automagik-hive=={{VERSION}}

# Or run directly with uvx (recommended)
uvx automagik-hive@{{VERSION}} --version
\```

---

## 📋 Release Assets

- Python wheel (`.whl`) for fast installation
- Source distribution (`.tar.gz`) for building from source
- Digital attestations for supply chain security

---

## 🔗 Links

- 📦 [PyPI Package](https://pypi.org/project/automagik-hive/{{VERSION}}/)
- 📚 [Documentation](https://github.com/{{REPOSITORY}}/blob/main/README.md)
- 📝 [Full Changelog](https://github.com/{{REPOSITORY}}/compare/v0.1.1b2...v{{VERSION}})

---

🤖 **Automated Release**: Published via GitHub Actions using [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)

**Co-Authored-By**: Automagik Genie 🧞 <genie@namastex.ai>
```
