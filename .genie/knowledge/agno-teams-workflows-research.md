# Agno Multi-Agent Coordination Research
**Research Date:** 2025-10-30
**Source:** Agno Cookbook (https://github.com/agno-agi/agno/tree/main/cookbook)

---

## Executive Summary

Agno provides a sophisticated multi-agent coordination framework through **Teams** and **Workflows**. Teams enable autonomous agent collaboration with intelligent routing, while Workflows provide step-based orchestration with support for sequential, parallel, conditional, and iterative execution patterns.

**Key Findings:**
- Teams support 3 primary modes: `route`, `coordinate`, and `collaborate`
- Session state enables context sharing across agents and workflow steps
- Workflows 2.0 provides 5 core patterns: Sequential, Parallel, Conditional, Loop, and Router
- All patterns support both synchronous and streaming execution modes

---

## Part 1: Teams - Multi-Agent Coordination

### 1.1 Team Creation Fundamentals

**Basic Team Structure:**

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.hackernews import HackerNewsTools
from agno.tools.newspaper4k import Newspaper4kTools

# Create specialized agents
hn_researcher = Agent(
    name="HackerNews Researcher",
    model=OpenAIChat("gpt-4-mini"),
    role="Gets top stories from hackernews.",
    tools=[HackerNewsTools()],
)

article_reader = Agent(
    name="Article Reader",
    model=OpenAIChat("gpt-4-mini"),
    role="Reads articles from URLs.",
    tools=[Newspaper4kTools()],
)

# Create coordinated team
hn_team = Team(
    name="HackerNews Team",
    model=OpenAIChat("gpt-4-mini"),
    members=[hn_researcher, article_reader],
    instructions=[
        "First, search hackernews for what the user is asking about.",
        "Then, ask the article reader to read the links for the stories.",
        "Important: you must provide the article reader with the links to read.",
        "Finally, provide a thoughtful and engaging summary.",
    ],
    add_member_tools_to_context=False,
    markdown=True,
    show_members_responses=True,
)

# Execute team
hn_team.print_response(
    input="Write an article about the top 2 stories on hackernews",
    stream=True
)
```

**Setup Requirements:**
```bash
pip install openai ddgs newspaper4k lxml_html_clean agno
```

### 1.2 Team Modes and Routing Strategies

#### Mode 1: Router Teams (`respond_directly=True`)

**Purpose:** Route requests to specialized agents based on input analysis

**Pattern:**
```python
# Language routing example
language_team = Team(
    name="Language Router",
    model=OpenAIChat("gpt-4-mini"),
    members=[english_agent, spanish_agent, french_agent, german_agent],
    instructions=[
        "You are a language router that directs questions to the appropriate language agent.",
        "Detect the language of the user's question.",
        "Forward to the correct language specialist.",
    ],
    respond_directly=True,  # Members respond directly to user
    show_members_responses=True,
)
```

**How Routing Works:**
1. **Language Detection**: Team leader analyzes incoming input
2. **Member Selection**: Routes to appropriate specialist
3. **Direct Response**: Selected agent responds in target language
4. **Fallback Handling**: Team handles unsupported languages gracefully

**Key Configuration:**
- `respond_directly=True` - Enables direct member responses
- `show_members_responses=True` - Makes routing transparent

#### Mode 2: Cooperation Teams (`delegate_task_to_all_members=True`)

**Purpose:** Parallel research with consensus-building

**Pattern:**
```python
# Multi-source research team
research_team = Team(
    name="Research Coordinator",
    model=OpenAIChat("gpt-4-mini"),
    members=[reddit_researcher, hackernews_researcher],
    instructions=[
        "Coordinate research across different online communities.",
        "Get diverse perspectives from different platforms.",
        "Cross-reference information and reach consensus through discussion.",
    ],
    delegate_task_to_all_members=True,  # All members work simultaneously
    show_members_responses=True,
)
```

**Collaboration Flow:**
1. **Simultaneous Distribution**: All agents receive the same task
2. **Specialized Investigation**: Each uses domain-specific tools
3. **Information Synthesis**: Agents discuss and refine perspectives
4. **Facilitated Coordination**: Team leader moderates consensus-building

#### Mode 3: Coordinate/Collaborate Mode

**Purpose:** Sequential delegation with leader coordination

**Default Behavior:**
- Team leader analyzes request
- Delegates to appropriate members sequentially
- Synthesizes responses into unified output
- Used when `respond_directly=False` (default)

### 1.3 Session State and History Management

#### Pattern 1: Team-Level Shared History

**Purpose:** All members access complete team conversation history

```python
from agno.storage.db.sqlite import SqliteDb

multi_lingual_team = Team(
    name="Multi-Lingual Q&A",
    model=OpenAIChat("gpt-4-mini"),
    members=[german_agent, spanish_agent, french_agent],
    db=SqliteDb(db_file="tmp/team_history.db"),
    add_team_history_to_members=True,  # Share full history
    respond_directly=True,
)

# First interaction (German)
multi_lingual_team.print_response(
    input="Hallo, wie heißt du? Meine Name ist John.",
    session_id="user_session_123"
)

# Follow-up (Spanish) - retains context from German interaction
multi_lingual_team.print_response(
    input="Cuéntame una historia de 2 oraciones usando mi nombre real",
    session_id="user_session_123"  # Same session maintains context
)
```

**Benefits:**
- Context retention across language switches
- Seamless multi-turn conversations
- Persistent session management

#### Pattern 2: Direct Response with History

**Purpose:** Stateful conversations with specialized routing

```python
geo_search_team = Team(
    name="Geo Search Team",
    model=OpenAIChat("o3-mini"),
    respond_directly=True,
    members=[weather_agent, news_agent, activities_agent],
    db=SqliteDb(db_file="tmp/geo_search_team.db"),
    add_history_to_context=True,  # Leader knows previous requests
)

# First request
geo_search_team.print_response(
    input="What's the weather in Tokyo?",
    session_id="session_001"
)

# Follow-up with context reference
geo_search_team.print_response(
    input="What are the top news in that city?",  # "that city" = Tokyo
    session_id="session_001"
)
```

**How It Works:**
1. Database stores conversation records
2. `add_history_to_context=True` provides context awareness
3. Subsequent queries reference prior interactions
4. Member specialization with shared context

#### Pattern 3: Session State Injection

**Purpose:** Pass custom state variables to agent instructions

```python
from agno.storage.db.inmemory import InMemoryDb

personalized_team = Team(
    name="Personalized Assistant",
    model=OpenAIChat("gpt-4-mini"),
    members=[support_agent, sales_agent],
    db=InMemoryDb(),
    add_session_state_to_context=True,  # Inject state into instructions
)

# Use state variables in agent instructions
support_agent.instructions = [
    "You are helping {user_name} who is {age} years old.",
    "Provide age-appropriate support.",
]

# First call with state initialization
personalized_team.print_response(
    input="I need help with my account",
    session_id="user_789",
    session_state={"user_name": "John", "age": 30}
)

# Subsequent calls auto-load state
personalized_team.print_response(
    input="Can you explain the process again?",
    session_id="user_789"  # State automatically retrieved
)
```

**Key Features:**
- `session_state` parameter populates context variables
- `add_session_state_to_context=True` enables templating
- `session_id`/`user_id` enable state lookup

#### Pattern 4: Nested Teams with Shared State

**Purpose:** Hierarchical teams with unified session state

```python
# Child teams
shopping_mgmt_team = Team(
    name="Shopping Management Team",
    members=[item_adder_agent, item_remover_agent],
    instructions=["Manage shopping list modifications."],
)

meal_planning_team = Team(
    name="Meal Planning Team",
    members=[meal_planner_agent],
    instructions=["Plan meals and suggest ingredients."],
)

# Parent team with shared state
shopping_team = Team(
    name="Shopping List Team",
    session_state={"shopping_list": [], "chores": []},  # Single source of truth
    members=[shopping_mgmt_team, meal_planning_team],
    instructions=[
        "Coordinate shopping and meal planning.",
        "Maintain unified shopping list.",
        "Log all actions to chores list.",
    ],
)
```

**State Flow Architecture:**
1. **Single Source of Truth**: Parent initializes and maintains state
2. **Propagation**: Child teams receive `session_state` parameter
3. **No Isolation**: All teams reference identical state object
4. **Transparent Access**: Agents modify shared dictionaries directly

**Tool Example:**
```python
def add_item(session_state, item: str) -> str:
    """Add item to shared shopping list"""
    session_state["shopping_list"].append(item)
    session_state["chores"].append(f"Added {item} to list")
    return f"Added {item} successfully"
```

### 1.4 Team Coordination Patterns Summary

| Pattern | Use Case | Key Config | Benefits |
|---------|----------|------------|----------|
| **Router** | Specialized routing | `respond_directly=True` | Direct specialist access |
| **Cooperation** | Parallel research | `delegate_task_to_all_members=True` | Diverse perspectives |
| **Coordinate** | Sequential delegation | Default mode | Unified synthesis |
| **Shared History** | Context retention | `add_team_history_to_members=True` | Multi-turn awareness |
| **Direct + History** | Stateful routing | `respond_directly=True` + `add_history_to_context=True` | Contextual specialization |
| **Session State** | Custom variables | `add_session_state_to_context=True` | Personalization |
| **Nested State** | Hierarchical teams | `session_state` at parent | Unified state management |

---

## Part 2: Workflows - Step-Based Orchestration

### 2.1 Workflow Fundamentals

**Workflows 2.0 Features:**
- Step-based execution (agents, teams, or functions)
- Sequential, parallel, conditional, and loop patterns
- Session state sharing across steps
- Streaming support with real-time events
- Database persistence (PostgreSQL/SQLite)

**Basic Pattern:**
```python
from agno.workflow import Workflow, Step
from agno.storage.db.sqlite import SqliteDb

workflow = Workflow(
    name="Content Creation Pipeline",
    steps=[
        Step("Research", team=research_team),
        Step("Write", agent=writer_agent),
        Step("Review", agent=reviewer_agent),
    ],
    db=SqliteDb(db_file="tmp/workflow.db"),
)

workflow.print_response(input="Create article about AI trends", stream=True)
```

### 2.2 Five Core Workflow Patterns

#### Pattern 1: Sequential Workflows

**Purpose:** Linear processes with dependencies

**Example:**
```python
from agno.workflow import Workflow, Step
from agno.models.openai import OpenAIChat

# Agents
hn_agent = Agent(name="HN Agent", tools=[HackerNewsTools()])
web_agent = Agent(name="Web Agent", tools=[GoogleSearch()])
planner_agent = Agent(name="Content Planner", model=OpenAIChat("gpt-4o"))

# Team for parallel research
research_team = Team(
    name="Research Team",
    members=[hn_agent, web_agent],
    instructions=["Research the topic thoroughly using all tools."],
)

# Sequential workflow
content_workflow = Workflow(
    name="Content Creation",
    steps=[
        Step("Research", team=research_team),  # Step 1: Multi-agent research
        Step("Plan", agent=planner_agent),     # Step 2: Planning from research
    ],
    db=SqliteDb(db_file="tmp/workflow.db"),
)

content_workflow.print_response(
    input="AI trends in 2024",
    stream=True,
    markdown=True
)
```

**Flow:**
```
Research Team (parallel agents) → Content Planner
```

**When to Use:**
- Linear dependencies between steps
- Output of one step feeds next step
- Ordered process execution

#### Pattern 2: Parallel Execution

**Purpose:** Independent tasks running simultaneously

**Example:**
```python
from agno.workflow import Workflow, Step, Parallel

# Agents
researcher = Agent(tools=[HackerNewsTools(), GoogleSearch()])
writer = Agent(name="Writer")
reviewer = Agent(name="Reviewer")

# Parallel workflow
parallel_workflow = Workflow(
    name="Parallel Content Creation",
    steps=[
        Parallel(
            Step("Research HN", agent=researcher, message="Search HackerNews for {input}"),
            Step("Research Web", agent=researcher, message="Search web for {input}"),
            name="Research Phase"
        ),
        Step("Write", agent=writer),
        Step("Review", agent=reviewer),
    ],
)

parallel_workflow.print_response(input="Recent AI developments", stream=True)
```

**Flow:**
```
┌─ Research HN ──┐
│                 ├─→ Write Article → Review
└─ Research Web ─┘
```

**Benefits:**
- Time savings through concurrent execution
- Multiple source research
- Independent task optimization

**When to Use:**
- Tasks don't depend on each other
- Multiple data sources
- Speed optimization needed

#### Pattern 3: Conditional Execution

**Purpose:** Execute steps based on business logic

**Example:**
```python
from agno.workflow import Workflow, Step, Parallel, Condition

# Agents
hn_agent = Agent(name="HN Agent", tools=[HackerNewsTools()])
exa_agent = Agent(name="Deep Researcher", tools=[ExaTools()])
trend_agent = Agent(name="Trend Analyzer")
fact_checker = Agent(name="Fact Checker")
writer = Agent(name="Content Writer")

# Condition evaluators
def check_if_we_should_search_hn(step_input) -> bool:
    """Check if topic is tech-related"""
    tech_keywords = ["startup", "AI", "programming", "tech", "blockchain"]
    return any(keyword.lower() in step_input.message.lower()
               for keyword in tech_keywords)

def check_if_comprehensive_research_needed(step_input) -> bool:
    """Check if comprehensive analysis requested"""
    comprehensive_keywords = ["comprehensive", "detailed", "in-depth", "thorough"]
    return any(keyword.lower() in step_input.message.lower()
               for keyword in comprehensive_keywords)

# Conditional workflow
conditional_workflow = Workflow(
    name="Adaptive Research",
    steps=[
        Parallel(
            # Condition 1: Tech topics → HackerNews
            Condition(
                name="HackerNewsCondition",
                evaluator=check_if_we_should_search_hn,
                steps=[Step("HN Research", agent=hn_agent)],
            ),
            # Condition 2: Comprehensive → Multi-step analysis
            Condition(
                name="ComprehensiveResearchCondition",
                evaluator=check_if_comprehensive_research_needed,
                steps=[
                    Step("Deep Analysis", agent=exa_agent),
                    Step("Trend Analysis", agent=trend_agent),
                    Step("Fact Check", agent=fact_checker),
                ],
            ),
        ),
        Step("Write Content", agent=writer),
    ],
)

conditional_workflow.print_response(
    input="Comprehensive analysis of climate change research",
    stream=True
)
```

**Flow:**
```
Input Analysis
    ├─ Condition 1: Tech? → HackerNews Research
    └─ Condition 2: Comprehensive? → [Deep Analysis → Trend → Fact Check]
                                                        ↓
                                                  Write Content
```

**When to Use:**
- Topic-specific workflows
- Adaptive processing depth
- Resource optimization

#### Pattern 4: Loop/Iteration Workflows

**Purpose:** Iterative refinement with quality checks

**Example:**
```python
from agno.workflow import Workflow, Step, Loop

# Agents
hn_researcher = Agent(tools=[HackerNewsTools()])
web_researcher = Agent(tools=[GoogleSearch()])
content_creator = Agent(name="Content Creator")

# Evaluator function
def research_evaluator(step_input) -> bool:
    """Check if we have enough research data"""
    # Exit loop if substantial content gathered
    if step_input.previous_step_content:
        total_length = sum(len(str(content)) for content in step_input.previous_step_content)
        if total_length > 200:  # Threshold for sufficient research
            print(f"✓ Research complete: {total_length} characters gathered")
            return True
    return False

# Loop workflow
loop_workflow = Workflow(
    name="Iterative Research",
    steps=[
        Loop(
            steps=[
                Step("Research HN", agent=hn_researcher),
                Step("Research Web", agent=web_researcher),
            ],
            end_condition=research_evaluator,
            max_iterations=3,  # Safety limit
            name="Research Loop"
        ),
        Step("Create Content", agent=content_creator),
    ],
)

loop_workflow.print_response(input="AI breakthroughs", stream=True)
```

**Flow:**
```
┌─────────────────────────┐
│ Research HN → Web       │
│         ↓               │
│   Check Condition       │
│    ├─ Met? → Exit       │
│    └─ No? → Repeat ────┘
↓
Create Content
```

**When to Use:**
- Quality-driven processes
- Iterative refinement
- Retry logic
- Data accumulation until threshold

#### Pattern 5: Router/Conditional Branching

**Purpose:** Dynamic routing based on content analysis

**Example:**
```python
from agno.workflow import Workflow, Step, Router

# Agents
hn_researcher = Agent(tools=[HackerNewsTools()])
web_researcher = Agent(tools=[GoogleSearch()])
publisher = Agent(name="Publisher")

# Router function
def research_router(step_input) -> Step:
    """Route to appropriate research method based on topic"""
    tech_keywords = ["startup", "AI", "programming", "tech", "blockchain"]
    topic = step_input.message.lower()

    if any(keyword in topic for keyword in tech_keywords):
        print("→ Routing to HackerNews (tech topic detected)")
        return Step("HN Research", agent=hn_researcher)
    else:
        print("→ Routing to Web Search (general topic)")
        return Step("Web Research", agent=web_researcher)

# Router workflow
router_workflow = Workflow(
    name="Smart Research Router",
    steps=[
        Router(
            name="Research Router",
            evaluator=research_router,
        ),
        Step("Publish", agent=publisher),
    ],
)

# Tech topic → HackerNews
router_workflow.print_response(input="Latest AI startup funding", stream=True)

# General topic → Web Search
router_workflow.print_response(input="Climate change solutions", stream=True)
```

**Flow:**
```
Input → Router Evaluation
            ├─ Path A: HackerNews Research ─┐
            └─ Path B: Web Research ─────────┤
                                             ↓
                                        Publishing
```

**When to Use:**
- Complex decision trees
- Topic-specific workflows
- Dynamic routing logic
- Different processing pipelines

### 2.3 Custom Function Steps

**Purpose:** Mix agent intelligence with programmatic control

**Example:**
```python
from agno.workflow import Workflow, Step, StepInput, StepOutput

def custom_content_planning_function(step_input: StepInput) -> StepOutput:
    """Custom Python function as workflow step"""

    # Access previous step content
    research_results = step_input.previous_step_content

    # Process with custom logic
    plan = f"""
    Content Plan based on research:

    Week 1: Introduction based on {research_results[0][:100]}...
    Week 2: Deep dive into findings
    Week 3: Expert perspectives
    Week 4: Conclusion and future trends

    3 posts per week, total 12 posts
    """

    return StepOutput(content=plan)

# Workflow mixing agents and functions
hybrid_workflow = Workflow(
    name="Hybrid Workflow",
    steps=[
        Step("Research", team=research_team),  # Agent-based
        Step("Plan", function=custom_content_planning_function),  # Function-based
    ],
    db=SqliteDb(db_file="tmp/hybrid.db"),
)

hybrid_workflow.print_response(input="AI trends 2024", stream=True)
```

**StepInput Features:**
- `step_input.message` - Current input message
- `step_input.previous_step_content` - Previous step outputs
- `step_input.workflow_session_state` - Shared workflow state
- `step_input.get_step_content(step_name)` - Access specific step output

**StepOutput Features:**
- `StepOutput(content=result)` - Return step result
- `StepOutput(stop=True)` - Early workflow termination
- Can include metadata and additional context

### 2.4 Workflow Session State Management

**Purpose:** Share data across workflow steps

**Pattern:**
```python
def step_with_state(step_input: StepInput) -> StepOutput:
    """Custom step accessing and modifying workflow state"""

    # Initialize state if needed
    if step_input.workflow_session_state is None:
        step_input.workflow_session_state = {}

    # Access shared state
    previous_data = step_input.workflow_session_state.get("analysis_results")

    # Process current step
    current_results = process_data(step_input.message, previous_data)

    # Update state for next steps
    step_input.workflow_session_state["analysis_results"] = current_results
    step_input.workflow_session_state["processed_count"] = \
        step_input.workflow_session_state.get("processed_count", 0) + 1

    return StepOutput(content=current_results)

# Workflow with session state
stateful_workflow = Workflow(
    name="Stateful Processing",
    steps=[
        Step("Analyze", function=step_with_state),
        Step("Refine", function=step_with_state),  # Accesses previous state
        Step("Finalize", function=step_with_state),  # Accesses accumulated state
    ],
)
```

**State Features:**
- Persists across all workflow steps
- Shared dictionary available to all steps
- Enables progressive refinement
- Supports audit trails and metrics

### 2.5 Workflow Execution Modes

#### Synchronous Execution
```python
# Standard synchronous execution
response = workflow.run(message="Process this data")
print(response.content)
```

#### Async Execution
```python
# Asynchronous execution
response = await workflow.arun(message="Async process")
print(response.content)
```

#### Streaming Execution
```python
# Real-time streaming with events
for response in workflow.run(message="Stream process", stream=True):
    print(f"Step: {response.step_name}")
    print(f"Content: {response.content}")
    if response.step_output:
        print(f"Output: {response.step_output.content}")
```

### 2.6 Workflow Best Practices

| Pattern | Optimal Use | Avoid |
|---------|-------------|-------|
| **Sequential** | Linear dependencies | Independent tasks |
| **Parallel** | Speed optimization | Sequential requirements |
| **Conditional** | Topic-specific routing | Simple flows |
| **Loop** | Quality assurance | Known finite processes |
| **Router** | Complex decision logic | Basic if/else scenarios |
| **Mixed** | Complex requirements | Over-engineering simple tasks |

**Key Capabilities:**
- **State Sharing**: Use `session_state` for cross-step data
- **Streaming**: Enable real-time feedback with `stream=True`
- **Early Stopping**: Return `StepOutput(stop=True)` to halt
- **Step Access**: Use `get_step_content(step_name)` for specific outputs
- **Additional Context**: Pass metadata via `additional_data`

---

## Part 3: Integration Patterns

### 3.1 Teams in Workflows

**Pattern:** Use teams as workflow steps

```python
# Multi-team workflow
research_team = Team(members=[hn_agent, web_agent])
analysis_team = Team(members=[analyst_agent, fact_checker])
content_team = Team(members=[writer_agent, editor_agent])

integrated_workflow = Workflow(
    name="Multi-Team Content Pipeline",
    steps=[
        Step("Research", team=research_team),
        Step("Analysis", team=analysis_team),
        Step("Content", team=content_team),
    ],
)
```

**Benefits:**
- Combine team collaboration with workflow orchestration
- Multi-agent steps within linear flows
- Scalable team composition

### 3.2 Nested Teams with Workflows

**Pattern:** Workflows within team members

```python
# Workflow as team member capability
research_workflow = Workflow(steps=[
    Step("HN", agent=hn_agent),
    Step("Web", agent=web_agent),
])

# Team with workflow-powered member
research_agent = Agent(
    name="Research Agent",
    workflow=research_workflow,  # Agent executes workflow
)

orchestration_team = Team(
    name="Content Team",
    members=[research_agent, writer_agent, editor_agent],
)
```

### 3.3 Database Integration

**PostgreSQL (Production):**
```python
from agno.storage.db.postgres import PgDb

workflow = Workflow(
    db=PgDb(
        db_url="postgresql://user:pass@localhost:5432/agno",
        schema="agno",
        auto_upgrade_schema=True,
    ),
)
```

**SQLite (Development):**
```python
from agno.storage.db.sqlite import SqliteDb

workflow = Workflow(
    db=SqliteDb(
        db_file="tmp/workflow.db",
        auto_upgrade_schema=True,
    ),
)
```

---

## Part 4: Real-World Examples

### Example 1: Content Creation Pipeline

**Requirements:**
- Research from multiple sources
- Quality-driven iteration
- Parallel content generation
- Editorial review

**Implementation:**
```python
from agno.workflow import Workflow, Step, Parallel, Loop

# Agents
hn_researcher = Agent(tools=[HackerNewsTools()])
web_researcher = Agent(tools=[GoogleSearch()])
writer = Agent(name="Writer")
editor = Agent(name="Editor")
fact_checker = Agent(name="Fact Checker")

# Quality evaluator
def has_enough_research(step_input) -> bool:
    if step_input.previous_step_content:
        total = sum(len(str(c)) for c in step_input.previous_step_content)
        return total > 500
    return False

# Complete workflow
content_pipeline = Workflow(
    name="Content Creation Pipeline",
    steps=[
        # Iterative research phase
        Loop(
            steps=[
                Parallel(
                    Step("HN Research", agent=hn_researcher),
                    Step("Web Research", agent=web_researcher),
                ),
            ],
            end_condition=has_enough_research,
            max_iterations=3,
            name="Research Phase"
        ),
        # Parallel content creation
        Parallel(
            Step("Write Article", agent=writer),
            Step("Fact Check", agent=fact_checker),
            name="Content Phase"
        ),
        # Final review
        Step("Editorial Review", agent=editor),
    ],
    db=SqliteDb(db_file="tmp/content_pipeline.db"),
)

content_pipeline.print_response(
    input="Write about recent AI developments",
    stream=True,
    markdown=True
)
```

### Example 2: Customer Support Router

**Requirements:**
- Multi-lingual support
- Topic-based routing
- Context retention
- Escalation handling

**Implementation:**
```python
# Support agents
billing_agent = Agent(name="Billing Specialist")
technical_agent = Agent(name="Technical Support")
sales_agent = Agent(name="Sales Specialist")
escalation_agent = Agent(name="Manager")

# Router evaluator
def route_support_request(step_input) -> Step:
    message = step_input.message.lower()

    # Billing keywords
    if any(word in message for word in ["payment", "invoice", "billing", "charge"]):
        return Step("Billing", agent=billing_agent)

    # Technical keywords
    if any(word in message for word in ["error", "bug", "not working", "broken"]):
        return Step("Technical", agent=technical_agent)

    # Sales keywords
    if any(word in message for word in ["pricing", "upgrade", "plan", "purchase"]):
        return Step("Sales", agent=sales_agent)

    # Default escalation
    return Step("Escalation", agent=escalation_agent)

# Support workflow
support_workflow = Workflow(
    name="Customer Support",
    steps=[
        Router(name="Route Request", evaluator=route_support_request),
    ],
    db=PgDb(db_url=os.getenv("DATABASE_URL")),
)

# Multi-turn support with context
support_workflow.run(
    message="I can't process a payment",
    session_id="customer_123"
)

support_workflow.run(
    message="Still having the same issue",
    session_id="customer_123"  # Context retained
)
```

### Example 3: Multi-Stage Research System

**Requirements:**
- Adaptive research depth
- Source prioritization
- Quality validation
- Consensus building

**Implementation:**
```python
# Research agents
quick_researcher = Agent(tools=[DuckDuckGo()])
deep_researcher = Agent(tools=[ExaTools()])
academic_researcher = Agent(tools=[ArxivTools()])
validator = Agent(name="Validator")

# Evaluators
def needs_deep_research(step_input) -> bool:
    return any(w in step_input.message.lower()
               for w in ["comprehensive", "detailed", "academic"])

def quality_check(step_input) -> bool:
    # Check if research meets quality standards
    content = str(step_input.previous_step_content)
    return len(content) > 1000 and "source" in content.lower()

# Research workflow
research_system = Workflow(
    name="Adaptive Research",
    steps=[
        # Initial quick research
        Step("Quick Research", agent=quick_researcher),

        # Conditional deep dive
        Condition(
            evaluator=needs_deep_research,
            steps=[
                Parallel(
                    Step("Deep Analysis", agent=deep_researcher),
                    Step("Academic Search", agent=academic_researcher),
                ),
            ],
        ),

        # Quality loop
        Loop(
            steps=[Step("Validate", agent=validator)],
            end_condition=quality_check,
            max_iterations=2,
        ),
    ],
)
```

---

## Part 5: Performance and Scaling Considerations

### 5.1 Team Scaling

**Small Teams (2-3 agents):**
- Simple routing or coordination
- Use `respond_directly=True` for efficiency
- InMemoryDb for development

**Medium Teams (4-6 agents):**
- Mix of routing and cooperation
- SQLite for session persistence
- Implement history management

**Large Teams (7+ agents):**
- Nested team hierarchies
- PostgreSQL with connection pooling
- Careful state management
- Consider workflow orchestration

### 5.2 Workflow Optimization

**Sequential:**
- Minimize steps where possible
- Combine related operations
- Use caching for repeated operations

**Parallel:**
- Identify truly independent tasks
- Monitor resource usage
- Set reasonable parallelism limits

**Conditional:**
- Optimize evaluator functions
- Cache evaluation results
- Minimize redundant checks

**Loop:**
- Always set `max_iterations`
- Implement clear exit conditions
- Avoid nested loops when possible

### 5.3 Database Considerations

**Development:**
```python
# SQLite for development
db=SqliteDb(db_file="tmp/dev.db")
```

**Production:**
```python
# PostgreSQL with connection pooling
db=PgDb(
    db_url=os.getenv("DATABASE_URL"),
    pool_size=20,
    max_overflow=30,
    auto_upgrade_schema=True,
)
```

---

## Part 6: Key Takeaways and Recommendations

### Team Best Practices

1. **Choose the Right Mode:**
   - `respond_directly=True` for specialized routing
   - `delegate_task_to_all_members=True` for parallel research
   - Default mode for sequential coordination

2. **Manage State Effectively:**
   - Use `add_team_history_to_members=True` for shared context
   - Enable `add_history_to_context=True` for leader awareness
   - Implement `session_state` for custom variables
   - Leverage nested teams with unified state

3. **Optimize Member Configuration:**
   - Keep teams focused (3-5 members ideal)
   - Use `show_members_responses=True` for transparency
   - Set `add_member_tools_to_context=False` when not needed

4. **Database Strategy:**
   - InMemoryDb: Quick testing, no persistence
   - SQLiteDb: Development, simple deployments
   - PgDb: Production, high concurrency

### Workflow Best Practices

1. **Pattern Selection:**
   - Sequential: Dependencies between steps
   - Parallel: Independent, time-saving tasks
   - Conditional: Topic-specific processing
   - Loop: Quality-driven refinement
   - Router: Complex decision trees

2. **State Management:**
   - Use `workflow_session_state` for cross-step data
   - Access previous steps via `previous_step_content`
   - Implement custom functions for programmatic control

3. **Performance:**
   - Set `max_iterations` on all loops
   - Optimize evaluator functions
   - Use streaming for long-running workflows
   - Monitor database connections

4. **Error Handling:**
   - Implement clear exit conditions
   - Use `StepOutput(stop=True)` for early termination
   - Log workflow progress
   - Plan fallback strategies

### Integration Recommendations

1. **Teams + Workflows:**
   - Use teams as workflow steps for complex operations
   - Implement workflows within agents for specialized processing
   - Maintain clear separation of concerns

2. **State Consistency:**
   - Use same `session_id` across related calls
   - Implement proper state initialization
   - Clean up old sessions periodically

3. **Monitoring:**
   - Enable `stream=True` for real-time feedback
   - Log team and workflow decisions
   - Track performance metrics
   - Monitor database growth

---

## Conclusion

Agno's Teams and Workflows provide a comprehensive framework for multi-agent coordination:

**Teams** enable:
- Intelligent routing to specialists
- Parallel research with consensus
- Contextual multi-turn conversations
- Hierarchical agent organization

**Workflows** provide:
- Step-based orchestration
- Sequential, parallel, conditional, and iterative patterns
- Session state management
- Mix of agents, teams, and custom functions

**Key Differentiators:**
- **Autonomous Operation**: Teams maintain shared context automatically
- **Flexible Composition**: Mix agents, teams, and functions freely
- **Production-Ready**: Database persistence, streaming, error handling
- **Developer-Friendly**: Clear patterns, minimal boilerplate

**Recommended Starting Points:**
1. Simple routing → Router team with `respond_directly=True`
2. Research coordination → Cooperation team with parallel delegation
3. Sequential processing → Basic workflow with agent steps
4. Complex orchestration → Workflows with mixed patterns

**Scaling Path:**
Development → SQLite workflows → PostgreSQL teams → Nested hierarchies → Enterprise deployments

This research demonstrates that Agno provides mature, production-ready patterns for building sophisticated multi-agent systems with clear coordination semantics and robust state management.
