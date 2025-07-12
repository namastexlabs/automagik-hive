# Agno Storage Validation

**Status**: ✅ CONSOLIDATED REFERENCE ✅  
**Library**: `/context7/agno` (2552 code snippets)  
**Description**: Storage backends and parameter validation rules  
**Parent**: [Agno Patterns Index](@genie/reference/agno-patterns-index.md)  
**Consolidated from**:
- agno-storage-configuration.md
- agno-validation-rules.md

---

## Storage Configuration ✅ VERIFIED

> **See Also**: For SQL table schemas created by these storage backends, see [Database Schema](@genie/reference/database-schema.md)

### SQLite Storage (Default)
```yaml
sqlite_storage:
  # CLASS: SqliteStorage
  table_name: str                               # Required - Table name for sessions
  db_url: Optional[str]                         # Database URL
  db_file: Optional[str]                        # Database file path (if db_url not provided)
  db_engine: Optional[Engine]                   # Existing SQLAlchemy engine
  schema_version: int                           # Default: 1
  auto_upgrade_schema: bool                     # Default: False
  mode: Optional[Literal["agent", "team", "workflow"]] # Default: "agent"
  
  # NOTE: If none of db_url, db_file, db_engine provided, uses in-memory SQLite
```

### PostgreSQL Storage
```yaml
postgres_storage:
  # CLASS: PostgresStorage
  table_name: str                               # Required - Table name for sessions
  schema: Optional[str]                         # Default: "ai"
  db_url: Optional[str]                         # Database URL (required if no db_engine)
  db_engine: Optional[Engine]                   # Existing SQLAlchemy engine
  schema_version: int                           # Default: 1
  auto_upgrade_schema: bool                     # Default: False
  mode: Optional[Literal["agent", "team", "workflow"]] # Default: "agent"
  
  # NOTE: Either db_url or db_engine must be provided
```

### SingleStore Storage
```yaml
singlestore_storage:
  # CLASS: SingleStoreStorage
  table_name: str                               # Required - Table name
  schema: Optional[str]                         # Default: "ai"
  db_url: Optional[str]                         # Database URL (required if no db_engine)
  db_engine: Optional[Engine]                   # Existing SQLAlchemy engine
  schema_version: int                           # Default: 1
  auto_upgrade_schema: bool                     # Default: False
  mode: Optional[Literal["agent", "team", "workflow"]] # Default: "agent"
```

### MongoDB Storage
```yaml
mongodb_storage:
  # CLASS: MongoDbStorage
  collection_name: str                          # Required - MongoDB collection name
  db_url: str                                   # Required - MongoDB connection URL
  db_name: str                                  # Required - Database name
```

### YAML File Storage
```yaml
yaml_storage:
  # CLASS: YamlStorage
  dir_path: str                                 # Required - Directory path for YAML files
```

## Parameter Validation Rules ✅ VERIFIED

### Required vs Optional Parameters
```yaml
required_parameters:
  Team:
    - members: List[Union[Agent, Team]]         # ONLY required Team parameter
  
  Agent:
    - None                                      # ALL Agent parameters are optional with defaults
  
  Workflow:
    - None                                      # ALL Workflow parameters are optional
  
  Storage:
    SqliteStorage:
      - table_name: str                         # Required
    PostgresStorage:
      - table_name: str                         # Required
      - db_url OR db_engine                     # One required
    MongoDbStorage:
      - collection_name: str                    # Required
      - db_url: str                            # Required
      - db_name: str                           # Required
    YamlStorage:
      - dir_path: str                          # Required
```

### Parameter Dependencies ✅ VERIFIED
```yaml
parameter_dependencies:
  knowledge_search:
    condition: "search_knowledge=True"
    requirement: "knowledge parameter must be provided"
    
  agentic_context:
    condition: "enable_agentic_context=True"
    applies_to: "Team only"
    effect: "Allows team leader to maintain and update team context"
    
  storage_engines:
    postgres_singlestore:
      requirement: "Either db_url OR db_engine must be provided (not both)"
    sqlite:
      fallback: "Uses in-memory SQLite if no db_url, db_file, or db_engine provided"
      
  tool_choice_logic:
    no_tools: "tool_choice defaults to 'none'"
    with_tools: "tool_choice defaults to 'auto'"
```

### Validation Rules ✅ VERIFIED
```yaml
validation_rules:
  team_mode:
    type: "Literal['route', 'coordinate', 'collaborate']"
    validation: "Must be exactly one of these three values"
    
  references_format:
    type: "Literal['json', 'yaml']"
    validation: "Must be exactly 'json' or 'yaml'"
    
  storage_mode:
    type: "Literal['agent', 'team', 'workflow']"
    validation: "Must be exactly one of these three values"
    
  reasoning_steps:
    reasoning_min_steps: "Must be >= 1 (default: 1)"
    reasoning_max_steps: "Must be >= reasoning_min_steps (default: 10)"
    
  num_history_runs:
    type: "int"
    default: 3
    validation: "Must be positive integer"
    
  boolean_defaults:
    rule: "All boolean parameters default to False unless explicitly stated"
    exceptions:
      - "create_default_system_message: defaults to True"
      - "add_member_tools_to_system_message: defaults to True"
      - "resolve_context: defaults to True"
      - "parse_response: defaults to True"
      - "show_tool_calls: defaults to True"
      - "search_knowledge: defaults to True (only if knowledge provided)"

---

**Navigation**: [Index](@genie/reference/agno-patterns-index.md)
