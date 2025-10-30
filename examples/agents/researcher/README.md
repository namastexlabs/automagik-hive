# Research Assistant Agent Example

A thorough research assistant that finds, analyzes, and synthesizes information from the web.

## What This Agent Does

- Searches the web for credible information
- Analyzes and cross-references multiple sources
- Synthesizes findings into clear reports
- Cites all sources properly
- Acknowledges limitations and uncertainties

## Features

✅ **Multi-Source Search** - Queries from different angles
✅ **Source Verification** - Checks credibility and recency
✅ **Web Scraping** - Extracts content from pages
✅ **YouTube Analysis** - Includes video sources
✅ **Structured Reports** - Clear, well-organized output

## Quick Start

### 1. Configure Environment

Add to `.env`:

```bash
HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/hive
OPENAI_API_KEY=your_openai_key_here
```

### 2. Run the Agent

```python
from hive.scaffolder.generator import generate_agent_from_yaml

# Load agent
agent = generate_agent_from_yaml("examples/agents/researcher/config.yaml")

# Research a topic
response = agent.run(
    "Research the current state of AI agents in 2024. "
    "Focus on capabilities, limitations, and future trends."
)
print(response.content)
```

### 3. Example Output

```markdown
# Research Summary: AI Agents in 2024

## Key Findings

1. **Capabilities Have Expanded Significantly**
   - Multi-modal understanding (text, images, video) [1]
   - Long-term memory and context (100K+ tokens) [2]
   - Tool use and API integration now standard [3]

2. **Limitations Remain**
   - Hallucination still occurs (~5-10% of responses) [4]
   - Reasoning errors on complex multi-step tasks [5]
   - No true understanding or consciousness [6]

3. **Future Trends**
   - Agent-to-agent collaboration increasing [7]
   - Specialization over generalization [8]
   - Integration with business workflows [9]

## Detailed Analysis

### Current Capabilities
Modern AI agents can:
- Process and understand multiple formats (text, code, images)
- Use external tools and APIs to take actions
- Maintain conversation context over long interactions
- Learn from feedback within a session

[Detailed analysis continues...]

## Sources

1. "The State of AI Agents in 2024" - MIT Technology Review
   https://example.com/ai-agents-2024
   Published: January 2024

2. "Long Context Windows: A Game Changer" - OpenAI Blog
   https://example.com/long-context
   Published: December 2023

[More sources...]

## Limitations

- Most studies focus on English-language performance
- Limited data on production deployment challenges
- Conflicting definitions of "agent" vs. "assistant"
- Long-term reliability data not yet available
```

## Configuration Explained

### Model Choice

Uses `gpt-4o` because:
- Strong research and synthesis capabilities
- Good at evaluating source credibility
- Understands complex topics
- Balances speed and quality

### Temperature (0.5)

Mid-range temperature:
- Creative enough for comprehensive search
- Focused enough for accuracy
- Good for synthesis and analysis

### Tools

- **web_search** - DuckDuckGo for finding sources
- **web_scraper** - Extract content from web pages
- **file_reader** - Analyze uploaded documents
- **youtube_tools** - Search and analyze video content

## Use Cases

### 1. Topic Research

```python
agent.run(
    "Research quantum computing breakthroughs in 2024. "
    "Focus on practical applications."
)
```

### 2. Competitive Analysis

```python
agent.run(
    "Research our top 3 competitors: Company A, B, C. "
    "Compare features, pricing, and market position."
)
```

### 3. Literature Review

```python
agent.run(
    "Find recent academic papers on transformer architectures. "
    "Summarize key innovations and cite sources."
)
```

### 4. Market Research

```python
agent.run(
    "Research the market for AI-powered customer service tools. "
    "Include market size, growth trends, and key players."
)
```

## Research Quality Tips

### 1. Ask Specific Questions

❌ BAD: "Research AI"
✅ GOOD: "Research AI agent frameworks for Python, comparing features, performance, and ease of use"

### 2. Specify Constraints

```python
agent.run(
    "Research electric vehicle adoption rates. "
    "Focus on: "
    "- Data from 2022-2024 only"
    "- Include US, EU, and China"
    "- Prefer academic or government sources"
)
```

### 3. Request Comparisons

```python
agent.run(
    "Compare React, Vue, and Svelte for building SPAs. "
    "Evaluate: performance, learning curve, ecosystem, job market"
)
```

### 4. Ask for Multiple Perspectives

```python
agent.run(
    "Research remote work effectiveness. "
    "Include both pro and con perspectives with evidence."
)
```

## Customization

### Focus on Specific Sources

```yaml
instructions: |
  Prefer these source types:
  1. Academic papers (first choice)
  2. Official documentation
  3. Industry reports
  4. Reputable news (last resort)

  Avoid: blogs, forums, social media
```

### Adjust Detail Level

```yaml
settings:
  max_tokens: 1000  # Brief summaries
  # or
  max_tokens: 3000  # Comprehensive reports
```

### Add Domain Expertise

```yaml
instructions: |
  You are a research assistant specializing in [domain].

  Apply domain-specific evaluation criteria:
  - [Criterion 1]
  - [Criterion 2]
```

## Output Formats

### Summary Format

```python
agent.run(
    "Research topic X. Output as: "
    "1. Executive summary (2-3 sentences)"
    "2. Key findings (bullet points)"
    "3. Top 3 sources"
)
```

### Comparison Table

```python
agent.run(
    "Compare products A, B, C. "
    "Output as markdown table with columns: "
    "Feature, Product A, Product B, Product C"
)
```

### Timeline

```python
agent.run(
    "Research the history of topic X. "
    "Output as timeline with key milestones."
)
```

## Performance

- **Research Time**: 1-3 minutes per topic
- **Sources**: Typically 5-10 sources per query
- **Cost**: ~$0.05-0.20 per research session
- **Accuracy**: High (when sources are credible)

## Limitations

**What it's good at:**
- Finding publicly available information
- Synthesizing multiple perspectives
- Recent information (via web search)
- Factual topics with good sources

**What it struggles with:**
- Paywalled content (academic papers)
- Information requiring authentication
- Very niche topics with few sources
- Real-time data (stock prices, live events)

## Integration Examples

### Slack Research Bot

```python
@app.command("/research")
def research_command(ack, command, client):
    ack()
    query = command['text']

    # Run research
    result = agent.run(f"Research: {query}")

    # Post to Slack
    client.chat_postMessage(
        channel=command['channel_id'],
        text=result.content
    )
```

### Research Report Generator

```python
def generate_report(topic, output_file):
    """Generate PDF research report."""
    result = agent.run(f"Research: {topic}")

    # Convert markdown to PDF
    markdown_to_pdf(result.content, output_file)
```

### Competitive Intelligence

```python
def daily_competitor_scan(competitors):
    """Scan competitors daily for updates."""
    for competitor in competitors:
        result = agent.run(
            f"Find news and updates about {competitor} "
            f"from the last 24 hours"
        )
        save_to_database(competitor, result.content)
```

## Best Practices

### 1. Verify Critical Information

```python
# For important decisions, verify findings
result = agent.run("Research topic X")

# Then manually check top 3 sources
# Don't blindly trust AI research for critical decisions
```

### 2. Combine with Human Expertise

```python
# AI research = broad scan
# Human expert = deep dive on key areas

ai_research = agent.run("Research topic X")
human_review = expert.analyze(ai_research)
```

### 3. Update Research Regularly

```python
# Re-run research periodically for evolving topics
if topic_age > 30_days:
    updated_research = agent.run(f"Research: {topic}")
```

## Troubleshooting

### Low-Quality Sources

**Fix**: Add source filtering:

```yaml
instructions: |
  Reject sources that:
  - Have no author listed
  - Are older than 3 years
  - Come from unknown websites
  - Lack citations
```

### Biased Research

**Fix**: Explicitly request balanced views:

```yaml
instructions: |
  Always present multiple perspectives:
  - Mainstream view
  - Alternative views
  - Criticisms and limitations
```

### Hallucinated Sources

**Fix**: Verify source existence:

```yaml
instructions: |
  NEVER cite a source you didn't actually find.
  All URLs must be from actual web searches.
  If unsure, note "Source unavailable" instead.
```

## Next Steps

1. **Custom Sources** - Add preferred research databases
2. **Automated Reports** - Schedule regular research updates
3. **Team Integration** - Share research via Slack/email
4. **Knowledge Base** - Store research for future reference

## Learn More

- [Web Search Guide](../../../docs/web-search.md)
- [Source Evaluation](../../../docs/source-evaluation.md)
- [Research Best Practices](../../../docs/research.md)
