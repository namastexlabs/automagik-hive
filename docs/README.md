# Automagik Hive Documentation

## 🎯 Quick Start

**For Users:**
- [Main README](../README.md) - Getting started guide
- [Example Agents](../hive/examples/agents/QUICK_START.md) - Run working examples

**For Contributors:**
- [CLAUDE.md](../CLAUDE.md) - Development guidance
- [AGENTS.md](../AGENTS.md) - Agent architecture
- [CONTRIBUTING.md](../CONTRIBUTING.md) - How to contribute

---

## 📁 Documentation Structure

### Planning (docs/planning/)
- **hive-v2-the-great-obliteration-aftermath.md** - Original V2 redesign plan
- **HIVE_V2_README.md** - V2 feature overview

### Decisions (docs/decisions/)
- **DEPENDENCIES_CLEANUP.md** - Dependency reduction decisions
- **PYPROJECT_CHANGES_NEEDED.md** - Build configuration changes

### Reviews (docs/reviews/)
- **HONEST_V2_STATUS.md** - Current implementation status (what works/doesn't)
- **IMPLEMENTATION_SUMMARY.md** - Quick summary of today's work

### Examples (docs/examples/)
- **EXAMPLE_AGENTS_EVIDENCE.md** - Working agent demonstrations

---

## 🚀 What Actually Works

✅ **Meta-Agent Generation** - REAL AI using LLM calls (not keyword matching)
✅ **3 Working Examples** - Support bot, code reviewer, researcher
✅ **Production RAG** - Hash-based incremental loading
✅ **Clean Architecture** - No registries, no wrappers, direct Agno

See [HONEST_V2_STATUS.md](reviews/HONEST_V2_STATUS.md) for details.
