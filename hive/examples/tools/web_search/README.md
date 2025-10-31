# Web Search Tool

A wrapper around Agno's DuckDuckGoTools for searching the web and retrieving results with titles, URLs, and snippets.

## Overview

This tool provides web search capabilities:

- **Text Search** - Search the web for information
- **News Search** - Find recent news articles (optional)
- **Quick Answers** - Get instant answers to questions
- **Safe Search** - Filter inappropriate content
- **Regional Results** - Search with regional preferences
- **No API Key Required** - Uses DuckDuckGo (no authentication)

## When to Use This Tool

Use web search when:

- Gathering current information
- Research and fact-checking
- Finding recent news/updates
- Building knowledge bases
- Answering questions with web sources
- Competitive intelligence

**Examples:**
- Research agents
- Question answering systems
- News aggregators
- Competitive analysis
- Fact verification
- Current events monitoring

## Structure

```
web-search/
├── config.yaml     # Tool configuration
├── tool.py         # DuckDuckGo wrapper implementation
└── README.md       # This file
```

## Setup

### No Authentication Required

Unlike many search APIs, DuckDuckGo requires no API keys or authentication. The tool works out of the box.

### Configure Options

Edit `config.yaml`:

```yaml
parameters:
  max_results: 5           # Results per search
  include_snippets: true   # Include text snippets
  safe_search: true        # Filter content
  region: "us-en"          # Regional preference
  timeout_seconds: 30      # Request timeout

search_options:
  include_news: false      # Enable news search
  include_images: false    # Enable image search
  time_filter: null        # Time range filter
```

## Usage

### Basic Search

```python
from my_test_project.ai.tools.examples.web_search.tool import get_web_search_tool

# Create search tool
search = get_web_search_tool()

# Execute search
result = search.search("Python programming")

if result["status"] == "success":
    print(f"Found {result['total_results']} results")

    for res in result["results"]:
        print(f"\nTitle: {res['title']}")
        print(f"URL: {res['url']}")
        print(f"Snippet: {res['snippet']}")
```

### Custom Result Count

```python
# Override default max_results
result = search.search(
    query="machine learning tutorials",
    max_results=10  # Get 10 results instead of default 5
)
```

### Safe Search Control

```python
# Disable safe search
result = search.search(
    query="sensitive topic",
    safe_search=False
)
```

### Quick Answers

```python
# Get instant answer for factual questions
result = search.quick_answer("What is the capital of Japan?")

if result["status"] == "success":
    print(f"Question: {result['query']}")
    print(f"Answer: {result['answer']}")
    print(f"Source: {result['source']}")
```

### Search and Summarize

```python
# Get formatted summary of results
summary = search.search_and_summarize("artificial intelligence 2024")

print(summary)
# Output:
# Search Results for: artificial intelligence 2024
# Found 5 results
#
# 1. Title here
#    https://example.com
#    Snippet text...
```

### News Search

Enable in `config.yaml`:
```yaml
search_options:
  include_news: true
```

Then use:
```python
result = search.search_news("tech industry news")

for article in result["results"]:
    print(f"{article['title']}: {article['url']}")
```

## Integration with Agents

### Research Agent with Web Search

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from my_test_project.ai.tools.examples.web_search.tool import get_web_search_tool

def get_research_agent(**kwargs):
    search_tool = get_web_search_tool()

    def search_web(query: str, max_results: int = 5):
        """Search the web for information."""
        result = search_tool.search(query, max_results=max_results)
        if result["status"] == "success":
            return result["results"]
        return []

    return Agent(
        name="Web Researcher",
        model=OpenAIChat(id="gpt-4o-mini"),
        tools=[search_web],
        instructions="""You are a research agent with web search capabilities.
        Use search_web to find current information on any topic.""",
        **kwargs
    )

# Usage
agent = get_research_agent()
response = agent.run("What are the latest developments in quantum computing?")
```

### Workflow with Web Research

```python
from agno.workflow import Workflow, Step, StepOutput
from my_test_project.ai.tools.examples.web_search.tool import get_web_search_tool

search_tool = get_web_search_tool()

def research_step(step_input) -> StepOutput:
    """Research topic using web search."""
    topic = step_input.message

    # Search for information
    result = search_tool.search(topic, max_results=5)

    if result["status"] == "success":
        # Store findings in workflow state
        if step_input.workflow_session_state is None:
            step_input.workflow_session_state = {}

        step_input.workflow_session_state["search_results"] = result["results"]

        # Format findings
        findings = f"Research on: {topic}\n\n"
        for i, res in enumerate(result["results"], 1):
            findings += f"{i}. {res['title']}\n   {res['url']}\n"

        return StepOutput(content=findings)
    else:
        return StepOutput(content=f"Search failed: {result['error']}")

workflow = Workflow(
    name="Web Research Workflow",
    steps=[Step(name="Research", function=research_step)]
)
```

## Search Result Format

```python
{
    "status": "success",
    "query": "Python programming",
    "total_results": 5,
    "safe_search": true,
    "results": [
        {
            "title": "Python Programming Language",
            "url": "https://www.python.org",
            "snippet": "Official Python documentation and resources...",
            "source": "DuckDuckGo"
        },
        # ... more results
    ]
}
```

## Advanced Features

### Batch Searches

```python
queries = [
    "Python best practices",
    "JavaScript frameworks 2024",
    "Machine learning libraries"
]

results = []
for query in queries:
    result = search.search(query, max_results=3)
    if result["status"] == "success":
        results.extend(result["results"])

print(f"Total results from {len(queries)} searches: {len(results)}")
```

### Result Filtering

```python
def filter_by_domain(results: List[Dict], domain: str) -> List[Dict]:
    """Filter results by domain."""
    return [r for r in results if domain in r["url"]]

result = search.search("Python tutorials")
if result["status"] == "success":
    # Only show results from python.org
    official_results = filter_by_domain(result["results"], "python.org")
```

### Error Handling

```python
try:
    result = search.search("complex query")

    if result["status"] == "success":
        # Process results
        for res in result["results"]:
            print(res["title"])
    else:
        # Handle search error
        print(f"Search error: {result['error']}")
        print(f"Query was: {result['query']}")

except Exception as e:
    print(f"Unexpected error: {e}")
```

### Custom Result Processing

```python
def extract_urls(search_result: Dict) -> List[str]:
    """Extract just URLs from search results."""
    if search_result["status"] == "success":
        return [r["url"] for r in search_result["results"]]
    return []

result = search.search("data science courses")
urls = extract_urls(result)
print(f"Found {len(urls)} URLs")
```

## Configuration Options

### Result Limits

```yaml
parameters:
  max_results: 5  # Default: 5, Range: 1-20
```

### Safe Search

```yaml
parameters:
  safe_search: true  # Filter inappropriate content
```

### Regional Search

```yaml
parameters:
  region: "us-en"  # Options: us-en, uk-en, de-de, fr-fr, etc.
```

### News Search

```yaml
search_options:
  include_news: true  # Enable news search capability
```

### Timeout

```yaml
parameters:
  timeout_seconds: 30  # Request timeout
```

## Performance Considerations

### Rate Limiting

DuckDuckGo has implicit rate limits:
- Don't make rapid consecutive requests
- Add delays between searches if batch processing
- Consider caching results

```python
import time

for query in queries:
    result = search.search(query)
    # Add delay between searches
    time.sleep(1)
```

### Result Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str):
    """Cache search results."""
    return search.search(query)

# Subsequent calls with same query use cache
result1 = cached_search("Python")
result2 = cached_search("Python")  # Uses cached result
```

### Optimize Result Count

```python
# Don't fetch more than needed
result = search.search("topic", max_results=3)  # Faster than 10

# Process results incrementally
for res in result["results"]:
    if meets_criteria(res):
        break  # Stop early if found what you need
```

## Testing

Run the standalone test:

```bash
cd /home/cezar/automagik/automagik-hive/my-test-project
python -m ai.tools.examples.web_search.tool
```

Expected output:
- Tool initialization
- Standard search test (3 results)
- Quick answer test
- Search and summarize test
- Results with titles, URLs, snippets

## Integration with Tool Registry

Add to your tool registry:

```python
from ai.tools.examples.web_search.tool import get_web_search_tool

tools = {
    "web-search": get_web_search_tool,
    # ... other tools
}
```

## Related Examples

- **research-workflow** - Use web search in research pipelines
- **slack-notifier** - Send search results to Slack
- **csv-analyzer** - Analyze search result data

## Best Practices

1. **Cache results** - Avoid redundant searches
2. **Handle errors gracefully** - Always check status
3. **Respect rate limits** - Add delays between searches
4. **Filter results** - Process only what you need
5. **Use quick_answer** - For factual questions
6. **Set appropriate max_results** - Balance speed vs coverage
7. **Enable safe search** - Filter inappropriate content
8. **Document queries** - Track what was searched

## Troubleshooting

**No results returned**
- Check query spelling
- Try broader search terms
- Verify internet connectivity
- Check if DuckDuckGo is accessible

**Timeout errors**
```yaml
# Increase timeout in config.yaml
parameters:
  timeout_seconds: 60  # Increase from 30
```

**Empty snippets**
- Some results may not have snippets
- Always check if snippet exists:
```python
snippet = res.get("snippet", "No description available")
```

**Regional results not working**
- Verify region code format (e.g., "us-en", "uk-en")
- DuckDuckGo may not honor all region requests

**Rate limit errors**
```python
import time

def search_with_retry(query, max_retries=3):
    for attempt in range(max_retries):
        result = search.search(query)
        if result["status"] == "success":
            return result
        time.sleep(2 ** attempt)  # Exponential backoff
    return {"status": "error", "error": "Max retries exceeded"}
```

## Advanced Usage

### Multi-Query Research

```python
def research_topic(main_query: str, related_queries: List[str]):
    """Research main topic and related queries."""
    all_results = []

    # Main search
    main_result = search.search(main_query, max_results=5)
    if main_result["status"] == "success":
        all_results.extend(main_result["results"])

    # Related searches
    for query in related_queries:
        result = search.search(query, max_results=3)
        if result["status"] == "success":
            all_results.extend(result["results"])
        time.sleep(1)  # Rate limiting

    return all_results

results = research_topic(
    "machine learning",
    ["neural networks", "deep learning", "AI applications"]
)
```

### Result Deduplication

```python
def deduplicate_results(results: List[Dict]) -> List[Dict]:
    """Remove duplicate URLs from results."""
    seen_urls = set()
    unique_results = []

    for result in results:
        url = result["url"]
        if url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(result)

    return unique_results
```

### Custom Scoring

```python
def score_result(result: Dict, keywords: List[str]) -> int:
    """Score result based on keyword presence."""
    score = 0
    text = f"{result['title']} {result['snippet']}".lower()

    for keyword in keywords:
        if keyword.lower() in text:
            score += 1

    return score

result = search.search("Python programming")
if result["status"] == "success":
    keywords = ["tutorial", "beginner", "guide"]
    scored = [(r, score_result(r, keywords)) for r in result["results"]]
    scored.sort(key=lambda x: x[1], reverse=True)

    print("Top results:")
    for res, score in scored[:3]:
        print(f"{res['title']} (score: {score})")
```

## Limitations

- **No API Authentication** - Cannot access premium features
- **Rate Limits** - Implicit limits on request frequency
- **Result Quality** - May vary by query complexity
- **No Image Search** - Text results only in basic config
- **Regional Variance** - Results may differ by region
- **No Real-time** - Results may lag by minutes/hours

## Alternatives

For production systems, consider:
- **Google Search API** - More comprehensive (requires API key)
- **Bing Search API** - Microsoft alternative (requires API key)
- **Brave Search API** - Privacy-focused (requires API key)
- **Tavily API** - AI-optimized search (requires API key)

DuckDuckGo is best for:
- Development and testing
- Projects without API key budgets
- Privacy-conscious applications
- Simple search needs

## Learn More

- [Agno DuckDuckGoTools Documentation](https://docs.agno.com/tools/duckduckgo)
- [DuckDuckGo Search Syntax](https://help.duckduckgo.com/duckduckgo-help-pages/results/syntax/)
- [DuckDuckGo Privacy Policy](https://duckduckgo.com/privacy)
- [Web Search Best Practices](https://docs.agno.com/guides/search)
