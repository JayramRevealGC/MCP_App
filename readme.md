# MCP Server Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [NLP Intent Processing](#nlp-intent-processing)
3. [Database Layer Components](#database-layer-components)
4. [Query Execution Process](#query-execution-process)
5. [MCP API Endpoints](#mcp-api-endpoints)
6. [Session Memory Management](#session-memory-management)
7. [Error Handling & Timeout Management](#error-handling--timeout-management)
8. [Deployment & Configuration](#deployment--configuration)
9. [Process Flow Diagrams](#process-flow-diagrams)

---

## Architecture Overview

The MCP (Model Context Protocol) Server is a domain-specific natural language to database query system designed for enterprise and company data operations in the AIES (Annual Integrated Economic Survey) database. The system enables users to interact with complex enterprise data using conversational language, with built-in support for session-based context management.

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   MCP Server    │    │   PostgreSQL    │
│   (Streamlit)   │◄──►│   (FastMCP)     │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │   (GPT-4o-mini) │
                       └─────────────────┘
```

### System Architecture Layers

1. **Presentation Layer**: Streamlit-based web interface with session management
2. **API Layer**: FastMCP server with HTTP transport and session support
3. **NLP Processing Layer**: Intent parsing with 6 specific query types for enterprise data
4. **Query Building Layer**: AIES-specific SQL construction with complex join patterns
5. **Data Access Layer**: Database connection and execution with timeout protection
6. **Storage Layer**: PostgreSQL AIES database with multiple schemas (space_meta, space_product_aies)

### Key Features

- **Domain-Specific Queries**: 6 specialized query types for enterprise/company data operations
- **Session-Based Context**: Remembers enterprise ID and company name across queries
- **Natural Language Processing**: Converts user queries into structured intents using GPT-4o-mini
- **Complex Join Patterns**: Handles multi-table joins across AIES database schemas
- **Flexible Filtering**: Supports enterprise ID, company name, dates, and variable comparisons
- **Timeout Protection**: Prevents long-running queries from blocking the system (60-second timeout)
- **Comprehensive Error Handling**: Validation, error reporting, and SQL query logging

---

## NLP Intent Processing

### Overview

The NLP intent processing system converts natural language queries into structured JSON intents specifically designed for enterprise and company data operations in the AIES database. This process uses OpenAI's GPT-4o-mini model to understand user intent and map it to one of 6 supported query types.

### Process Flow

```
User Query → OpenAI API → Intent JSON → Database Action → Results
     ↓
Session Memory (default ent_id/company_name)
```

### Intent Parser (`nlp_layer.py`)

**Function**: `parse_nl_to_intent(user_input: str, default_parameters: dict = None) -> dict`

**Process**:
1. **Input Processing**: Receives natural language query from user
2. **Default Parameters**: Applies session-based default enterprise ID or company name if not specified
3. **System Prompt**: Uses comprehensive prompt with examples for all 6 supported operations
4. **AI Processing**: Sends query to OpenAI GPT-4o-mini model with JSON response format
5. **Response Parsing**: Converts AI response to structured JSON intent
6. **Parameter Application**: Applies default parameters if missing from parsed intent
7. **Error Handling**: Returns fallback intent ("unknown") if parsing fails

**Supported Operations**:

| Operation | Description | Example Query |
|-----------|-------------|---------------|
| `fetch_data` | Fetch data for enterprise/company (all fields or specific variables) | "Show me all data for enterprise 000" |
| `compare_variables` | Compare two variables with percentage difference threshold | "Show x values where x differs from y by more than 20% for company ABC" |
| `filter_by_date` | Get companies that submitted on a specific date | "What companies submitted on 2023-09-20" |
| `count_units_kaus` | Count units and KAUs for a company/enterprise | "How many units and KAUs for enterprise 000" |
| `count_enterprises` | Count unique enterprises in the database | "How many unique enterprises are there" |
| `get_company_name` | Get company name for a specific enterprise ID | "What is the company name for enterprise 000" |
| `unknown` | Queries that don't match any supported type | Any unsupported operation |

### Intent Structure

#### Fetch Data Intent
```json
{
    "action": "fetch_data",
    "filters": {
        "variables": ["revenue", "profit"],  // Optional: specific fields to fetch
        "ent_id": "000"  // OR "company_name": "ABC Corp"
    }
}
```

#### Compare Variables Intent
```json
{
    "action": "compare_variables",
    "filters": {
        "variable_x": "revenue",
        "variable_y": "profit",
        "percentage_threshold": 0.2,  // 20% difference
        "company_name": "ABC Corp"  // OR "ent_id": "000"
    }
}
```

#### Filter by Date Intent
```json
{
    "action": "filter_by_date",
    "filters": {
        "submit_date": "2023-09-20"  // YYYY-MM-DD format
    }
}
```

#### Count Units/KAUs Intent
```json
{
    "action": "count_units_kaus",
    "filters": {
        "ent_id": "000"  // OR "company_name": "ABC Corp"
    }
}
```

#### Count Enterprises Intent
```json
{
    "action": "count_enterprises",
    "filters": {}
}
```

#### Get Company Name Intent
```json
{
    "action": "get_company_name",
    "filters": {
        "ent_id": "000"
    }
}
```

### Session-Based Default Parameters

The system supports session-based memory for default parameters:

- **Default Enterprise ID**: Once set, subsequent queries can omit `ent_id` specification
- **Default Company Name**: Once set, subsequent queries can omit `company_name` specification
- **Priority**: If both `ent_id` and `company_name` are available, `ent_id` takes precedence
- **Session Expiry**: Sessions expire after 24 hours of inactivity
- **Automatic Updates**: Default parameters are updated when new `ent_id` or `company_name` values are found in queries

### Key Features

- **Flexible Field Selection**: Fetch all fields or specify specific variables
- **Enterprise ID Priority**: When both `ent_id` and `company_name` are provided, `ent_id` is preferred
- **Date Format Conversion**: Automatically converts dates to YYYY-MM-DD format
- **Percentage Conversion**: Converts percentage thresholds to decimal (20% → 0.2)
- **Unknown Query Handling**: Returns "unknown" action for unsupported queries with helpful error messages

---

## Database Layer Components

### Overview

The database layer provides a robust, secure, and efficient interface to the AIES (Annual Integrated Economic Survey) PostgreSQL database. It consists of specialized modules working together to handle enterprise and company data operations safely, with support for complex multi-table joins across multiple schemas.

### Component Architecture

```
┌─────────────────┐
│   Executor      │ ← Main execution coordinator
├─────────────────┤
│   Query Builder │ ← SQL construction
├─────────────────┤
│   Connection    │ ← Database connectivity & timeout
└─────────────────┘
```

### 1. Connection Management (`connection.py`)

**Purpose**: Handles database connections and timeout management

**Key Functions**:
- `get_connection()`: Establishes PostgreSQL connection using environment variables
- `execute_with_timeout()`: Executes functions with 60-second timeout protection using threading
- `QueryTimeoutError`: Custom exception for timeout scenarios

**Configuration**:
```python
QUERY_TIMEOUT = 60  # seconds
```

**Environment Variables**:
- `PG_HOST`: Database host
- `PG_PORT`: Database port
- `PG_USER`: Database username
- `PG_PASSWORD`: Database password
- `PG_DATABASE`: Database name

### 2. Query Builder (`query_builder.py`)

**Purpose**: Constructs AIES-specific SQL queries from structured intents

**Key Features**:
- **Base Join Pattern**: Pre-configured complex join pattern across multiple schemas
- **Company Name Subqueries**: Efficient subquery pattern for company name filtering
- **Variable Selection**: Supports fetching all fields or specific variables
- **Enterprise ID Priority**: Prioritizes `ent_id` over `company_name` when both are provided

**Base Join Pattern**:
The system uses a standardized join pattern across multiple schemas:
- `space_meta.units` (a)
- `space_meta.product_refper_units` (b)
- `space_meta.product_refpers` (c)
- `space_meta.products` (d)
- `space_meta.refpers` (e)
- `space_product_aies.control_estabs` (f)
- `space_product_aies.item_estabs` (g)

**Query Builder Functions**:

#### `build_fetch_data_query(variables, company_name, ent_id)`
- Fetches all fields or specific variables for an enterprise/company
- Supports filtering by `ent_id` or `company_name`
- Uses subquery pattern for company name filtering

#### `build_compare_variables_query(variable_x, variable_y, percentage_threshold, company_name, ent_id)`
- Compares two variables with percentage difference threshold
- Uses ABS() and NULLIF() for safe percentage calculations
- Filters by enterprise or company

#### `build_filter_by_date_query(submit_date)`
- Finds companies that submitted on a specific date
- Uses subquery pattern to filter by `submit_date` in `control_contacts` table

#### `build_count_units_kaus_query(company_name, ent_id)`
- Counts distinct `reporting_id` (units) and `kau_id` (KAUs)
- Supports filtering by enterprise or company

#### `build_count_enterprises_query()`
- Counts distinct `ent_id` values across the database
- No filtering required

#### `build_get_company_name_query(ent_id)`
- Retrieves company name from `control_contacts` table
- Uses different join pattern optimized for company name lookup

### 3. Validation (`validation.py`)

**Purpose**: Provides validation utilities for database operations (currently minimal usage in AIES architecture)

**Key Functions**:
- `validate_columns()`: Validates column existence in tables
- `validate_join_columns()`: Validates join column existence
- `validate_order_by()`: Validates ORDER BY clauses
- `parse_condition()`: Parses flexible condition dictionaries

**Note**: The current AIES architecture uses pre-defined query patterns, so validation is primarily handled through query builder logic rather than generic validation functions.

### SQL Query Examples

#### Fetch Data Query (All Fields)
```sql
SELECT a.reporting_id, a.kau_id, a.login_id, a.ent_id, f.*, g.*
FROM space_meta.units a
INNER JOIN space_meta.product_refper_units b ON a.sscid = b.sscid
INNER JOIN space_meta.product_refpers c ON b.product_refper_id = c.id
INNER JOIN space_meta.products d ON d.id = c.product_id
INNER JOIN space_meta.refpers e ON e.id = c.refper_id
INNER JOIN space_product_aies.control_estabs f ON f.product_refper_unit_id = b.id
INNER JOIN space_product_aies.item_estabs g ON g.product_refper_unit_id = b.id
WHERE d.name = 'AIES'
  AND e.name = '2023'
  AND a.ent_id = %s
```

#### Compare Variables Query
```sql
SELECT revenue, profit
FROM space_meta.units a
INNER JOIN space_meta.product_refper_units b ON a.sscid = b.sscid
INNER JOIN space_meta.product_refpers c ON b.product_refper_id = c.id
INNER JOIN space_meta.products d ON d.id = c.product_id
INNER JOIN space_meta.refpers e ON e.id = c.refper_id
INNER JOIN space_product_aies.control_estabs f ON f.product_refper_unit_id = b.id
INNER JOIN space_product_aies.item_estabs g ON g.product_refper_unit_id = b.id
WHERE d.name = 'AIES'
  AND e.name = '2023'
  AND a.ent_id = %s
  AND ABS(revenue - profit) / NULLIF(profit, 0) > %s
```

### Security Features

- **Parameterized Queries**: All user inputs use parameterized queries (`%s` placeholders)
- **SQL Injection Prevention**: No direct string concatenation in SQL construction
- **Schema-Specific Queries**: Queries are scoped to specific schemas (`space_meta`, `space_product_aies`)
- **Timeout Protection**: 60-second query timeout prevents resource exhaustion

---

## Query Execution Process

### Overview

The query execution process coordinates all database operations, from intent parsing to result delivery. It ensures security, performance, and reliability through comprehensive validation, error handling, and SQL query logging.

### Execution Flow

```
Intent → Action Routing → SQL Construction → Validation → Execution → Result Processing → Response
```

### Main Executor (`executor.py`)

**Function**: `execute_action(action: str, filters: dict)`

**Process Steps**:

1. **Action Validation**
   - Handles "unknown" action without database connection
   - Returns helpful error message for unsupported queries

2. **SQL Query Construction**
   - Builds SQL query using query builder functions
   - Captures SQL and parameters for logging and error reporting
   - Handles build errors gracefully

3. **Connection Establishment**
   - Creates database connection using `get_connection()`
   - Sets up cursor with dictionary row factory
   - Implements connection cleanup in finally block

4. **Query Execution**
   - Executes SQL with timeout protection (60 seconds)
   - Handles result processing based on action type
   - Returns formatted results with SQL query information

5. **Error Handling**
   - Catches and formats database errors
   - Includes SQL query in error responses for debugging
   - Implements timeout protection with detailed error messages

### Action-Specific Processing

#### 1. Fetch Data (`fetch_data`)
**Process**:
1. Extract variables list (optional - if empty or None, fetch all fields)
2. Extract enterprise ID or company name (priority: ent_id > company_name)
3. Validate that at least one identifier is provided
4. Build SQL query using `build_fetch_data_query()`
5. Execute query and return all results

**Features**:
- Flexible field selection (all fields or specific variables)
- Supports filtering by enterprise ID or company name
- Enterprise ID takes precedence when both are provided

**Result Format**:
```json
[
    {
        "reporting_id": "...",
        "kau_id": "...",
        "ent_id": "...",
        "variable1": value1,
        "variable2": value2,
        ...
        "sql_query": "...",
        "sql_params": [...]
    }
]
```

#### 2. Compare Variables (`compare_variables`)
**Process**:
1. Extract variable_x, variable_y, and percentage_threshold
2. Extract company filter (ent_id or company_name)
3. Validate all required parameters are present
4. Build SQL query with percentage difference calculation
5. Execute query and return comparison results

**Features**:
- Percentage difference calculation using ABS() and NULLIF()
- Safe division handling (prevents division by zero)
- Filters by enterprise or company

**Result Format**:
```json
[
    {
        "variable_x": value1,
        "variable_y": value2,
        "sql_query": "...",
        "sql_params": [...]
    }
]
```

#### 3. Filter by Date (`filter_by_date`)
**Process**:
1. Extract submit_date from filters
2. Validate date format (YYYY-MM-DD)
3. Build SQL query using subquery pattern
4. Execute query and return enterprise IDs

**Features**:
- Date-based filtering using submit_date field
- Efficient subquery pattern for company identification

**Result Format**:
```json
[
    {
        "ent_id": "...",
        "sql_query": "...",
        "sql_params": [...]
    }
]
```

#### 4. Count Units/KAUs (`count_units_kaus`)
**Process**:
1. Extract enterprise ID or company name
2. Validate that at least one identifier is provided
3. Build SQL query with COUNT(DISTINCT) aggregations
4. Execute query and return single row with counts

**Features**:
- Counts distinct reporting IDs (units)
- Counts distinct KAU IDs (KAUs)
- Supports filtering by enterprise or company

**Result Format**:
```json
[
    {
        "Reporting_IDs": 123,
        "KAUs": 45,
        "sql_query": "...",
        "sql_params": [...]
    }
]
```

#### 5. Count Enterprises (`count_enterprises`)
**Process**:
1. Build SQL query with COUNT(DISTINCT ent_id)
2. Execute query and return single row with count

**Features**:
- Counts unique enterprises across entire database
- No filtering required

**Result Format**:
```json
[
    {
        "Enterprises": 5678,
        "sql_query": "...",
        "sql_params": []
    }
]
```

#### 6. Get Company Name (`get_company_name`)
**Process**:
1. Extract enterprise ID from filters
2. Validate enterprise ID is provided
3. Build SQL query using optimized join pattern
4. Execute query and return company name

**Features**:
- Optimized query pattern for company name lookup
- Uses different join pattern (control_contacts instead of control_estabs)

**Result Format**:
```json
[
    {
        "mail_addr_name1_txt": "Company Name",
        "sql_query": "...",
        "sql_params": [...]
    }
]
```

#### 7. Unknown Action (`unknown`)
**Process**:
1. Returns error message without database connection
2. No SQL query executed

**Result Format**:
```json
[
    {
        "message": "I'm sorry, but your query doesn't match any of the supported query types.",
        "action": "unknown",
        "sql_query": null,
        "sql_params": []
    }
]
```

### SQL Query Logging

All query results include SQL query information for debugging and transparency:

- **sql_query**: Formatted SQL query with parameter values (for display)
- **sql_params**: List of parameter values used in query

This allows users and developers to:
- Understand what SQL was executed
- Debug query issues
- Verify query correctness
- Optimize queries if needed

### Timeout Protection

**Implementation**:
- 60-second query timeout using threading
- `execute_with_timeout()` wrapper function
- `QueryTimeoutError` exception handling
- Graceful timeout response with SQL query information

**Benefits**:
- Prevents system blocking
- Protects against runaway queries
- Maintains system responsiveness
- Provides detailed error information including SQL

---

## MCP API Endpoints

### Overview

The MCP server exposes a single tool endpoint that handles all enterprise and company data operations through natural language processing with session-based context management.

### API Structure

**Base URL**: `http://host:8001/mcp`
**Transport**: Streamable HTTP
**Protocol**: Model Context Protocol (MCP)
**Session Support**: Yes (via `mcp-session-id` header)

### Available Tools

#### `query_users(user_query: str, session_id: str = None) -> dict`

**Description**: Main entry point for all database operations with session support

**Parameters**:
- `user_query` (str): Natural language query describing the desired database operation
- `session_id` (str, optional): Session identifier for context management

**Returns**:
```json
{
    "result": [
        // Array of database results or error objects
        // Each result includes sql_query and sql_params fields
    ]
}
```

**Process Flow**:
1. **Session Initialization**: Retrieves default parameters for session (if provided)
2. **Intent Parsing**: Convert natural language to structured intent with default parameters
3. **Session Update**: Updates session memory with new enterprise ID/company name if found
4. **Action Execution**: Execute database operation based on intent
5. **Result Formatting**: Return structured results with SQL query information

**Example Usage**:
```python
# Fetch data for enterprise
result = await query_users("Show me all data for enterprise 000", session_id="session_123")

# Subsequent query uses default enterprise ID
result = await query_users("Count units and KAUs", session_id="session_123")

# Compare variables
result = await query_users("Show revenue values where revenue differs from profit by more than 20% for company ABC", session_id="session_123")

# Filter by date
result = await query_users("What companies submitted on 2023-09-20")

# Count enterprises
result = await query_users("How many unique enterprises are there")

# Get company name
result = await query_users("What is the company name for enterprise 000")
```

### Server Configuration

**Core Setup** (`core.py`):
```python
mcp = FastMCP("nlp-db-server", host="0.0.0.0", port=8001)
```

**Tool Registration** (`tools.py`):
```python
@mcp.tool()
async def query_users(user_query: str, session_id: str = None) -> dict:
    default_params = get_default_parameters(session_id) if session_id else {}
    intent = await parse_nl_to_intent(user_query, default_params)
    
    if session_id:
        # Update session memory with new parameters
        update_default_parameters(session_id, intent.get("filters", {}))
    
    result = execute_action(intent["action"], intent.get("filters", {}))
    return {"result": result}
```

### Session Management

**Session ID**: Passed as parameter to `query_users` tool
- Client generates unique session ID (e.g., Streamlit session state)
- Server maintains session context in memory
- Sessions expire after 24 hours of inactivity

**Default Parameters**:
- Automatically applied to queries when not specified
- Updated when new enterprise ID or company name is found
- Priority: `ent_id` takes precedence over `company_name`

---

## Session Memory Management

### Overview

The system implements session-based memory management to remember default parameters (enterprise ID and company name) across queries within a session. This allows users to set context once and reference it in subsequent queries without repeating the enterprise ID or company name.

### Implementation (`memory.py`)

**Storage**: In-memory dictionary with session timestamps for expiry management

**Key Functions**:

#### `get_default_parameters(session_id: str) -> dict`
- Retrieves default parameters for a session
- Returns empty dict if session doesn't exist
- Automatically cleans up expired sessions

#### `update_default_parameters(session_id: str, parameters: dict) -> None`
- Updates default parameters for a session
- Only updates `ent_id` and `company_name` if present
- Updates session timestamp for expiry tracking

#### `clear_session(session_id: str) -> None`
- Clears all default parameters for a session
- Removes session from memory

### Session Configuration

**Session Expiry**: 24 hours of inactivity
- Sessions are automatically cleaned up when accessed
- Timestamps track last activity per session
- Expired sessions are removed to prevent memory leaks

### Usage Flow

1. **First Query**: User specifies enterprise ID or company name
   ```
   Query: "Show me all data for enterprise 000"
   Result: Data returned, ent_id="000" stored in session memory
   ```

2. **Subsequent Queries**: User can omit enterprise ID/company name
   ```
   Query: "Count units and KAUs"
   Result: Uses default ent_id="000" from session memory
   ```

3. **Parameter Update**: New enterprise ID/company name updates session
   ```
   Query: "Get data for company ABC Corp"
   Result: Data returned, company_name="ABC Corp" stored, replaces previous default
   ```

### Integration with NLP Layer

The NLP layer (`nlp_layer.py`) receives default parameters and:
1. Includes them in the prompt context if query doesn't specify enterprise/company
2. Applies defaults to parsed intent if missing
3. Prioritizes `ent_id` over `company_name` when both are available

### Integration with Tools Layer

The tools layer (`tools.py`) manages session memory:
1. Retrieves default parameters before intent parsing
2. Passes defaults to NLP layer
3. Updates session memory when new `ent_id` or `company_name` values are found
4. Only updates when new values are explicitly mentioned in queries

### Memory Structure

```python
_default_parameters = {
    "session_id_1": {
        "ent_id": "000",
        "company_name": "ABC Corp"
    },
    "session_id_2": {
        "ent_id": "123"
    }
}

_session_timestamps = {
    "session_id_1": datetime(2024, 1, 15, 10, 30, 0),
    "session_id_2": datetime(2024, 1, 15, 11, 45, 0)
}
```

### Benefits

- **Improved User Experience**: Users don't need to repeat enterprise/company identifiers
- **Context Preservation**: Maintains context across multiple queries
- **Flexible Updates**: Allows changing context mid-session
- **Memory Efficient**: Automatic cleanup prevents memory leaks
- **Session Isolation**: Each session maintains its own context

---

## Error Handling & Timeout Management

### Overview

The MCP server implements comprehensive error handling and timeout management to ensure system reliability and user experience.

### Error Categories

#### 1. Validation Errors
**Source**: Input validation functions
**Examples**:
- Invalid column names
- Non-existent tables
- Invalid operators
- Malformed conditions

**Handling**:
```python
try:
    validated_columns = validate_columns(table_name, columns)
except ValueError as e:
    return [{"error": str(e)}]
```

#### 2. Database Errors
**Source**: PostgreSQL execution
**Examples**:
- Connection failures
- SQL syntax errors
- Permission issues
- Data type mismatches

**Handling**:
```python
try:
    cur.execute(sql, params)
    rows = cur.fetchall()
    return [dict(row) for row in rows]
except Exception as e:
    return [{"error": f"Error executing query: {str(e)}"}]
```

#### 3. Timeout Errors
**Source**: Long-running queries
**Threshold**: 60 seconds
**Handling**:
```python
try:
    return execute_with_timeout(_execute_query)
except QueryTimeoutError as e:
    return [{"error": f"Query timeout: {str(e)}"}]
```

#### 4. Parsing Errors
**Source**: NLP intent parsing
**Examples**:
- Invalid JSON response
- Unrecognized intent
- Malformed filters
- Unsupported query types

**Handling**:
```python
try:
    intent_data = json.loads(response.choices[0].message.content)
    return intent_data
except Exception as e:
    logger.error(f"Error parsing intent: {e}", exc_info=True)
    return {"action": "unknown", "filters": {}}
```

#### 5. Action-Specific Errors
**Source**: Query builder and executor
**Examples**:
- Missing required parameters (ent_id, company_name, etc.)
- Invalid variable names
- Invalid date formats
- Missing filters for required actions

**Handling**:
```python
if not ent_id and not company_name:
    return [{
        "error": "Either enterprise ID or company name is required",
        "sql_query": None,
        "sql_params": []
    }]
```

### Timeout Management

#### Implementation Details

**Threading-Based Timeout**:
```python
def execute_with_timeout(func, *args, **kwargs):
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=QUERY_TIMEOUT)
    
    if thread.is_alive():
        raise QueryTimeoutError(f"Query execution timed out after {QUERY_TIMEOUT} seconds")
    
    if exception[0]:
        raise exception[0]
    
    return result[0]
```

**Benefits**:
- Prevents system blocking
- Maintains responsiveness
- Graceful degradation
- Resource protection

### Error Response Format

**Standard Error Format**:
```json
{
    "result": [
        {"error": "Descriptive error message"}
    ]
}
```

**Error Types**:
- Validation errors with specific field information
- Database errors with SQL context
- Timeout errors with duration information
- Parsing errors with fallback behavior

### Logging and Monitoring

**Error Logging**:
- Database connection errors
- Query execution failures
- Validation warnings
- Timeout occurrences

**Monitoring Points**:
- Query execution times
- Error rates by operation type
- Timeout frequency
- Database connection health

---

## Deployment & Configuration

### Overview

The MCP server is designed for containerized deployment with comprehensive configuration management and environment-based settings.

### Environment Configuration

#### Required Environment Variables

**Database Configuration** (`.env` file):
```bash
PG_HOST=your-database-host
PG_PORT=5432
PG_USER=your-username
PG_PASSWORD=your-password
PG_DATABASE=your-database-name
```

**OpenAI Configuration**:
```bash
OPENAI_API_KEY=your-openai-api-key
```

### Docker Deployment

#### Server Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "main.py"]
```

#### Client Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0"]
```

### Server Startup Process

#### Main Entry Point (`main.py`)

**Test Mode**:
```python
if len(sys.argv) > 1 and sys.argv[1] == "test":
    asyncio.run(test_query())
```

**Production Mode**:
```python
print("Starting MCP server...")
mcp.run(transport="streamable-http")
```

**Test Queries**:
```python
user_queries = [
    "Show me all data for enterprise 000",
    "Count units and KAUs for enterprise 000",
    "What companies submitted on 2023-09-20",
    "Show revenue values where revenue differs from profit by more than 20% for company ABC"
]
```

### Configuration Management

#### Server Configuration (`config.py`)
```python
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE = os.getenv("PG_DATABASE")
```

#### Client Configuration
```python
MCP_CONFIG = {
    "server_url": "http://54.164.108.181:8001/mcp",
    "timeout": 30,
    "tool_name": "query_users"
}

UI_CONFIG = {
    "logo_path": "RevealLabs_Logo.png",
    "default_chat_limit": 5,
    "max_chat_history": 100,
    "typing_indicator_delay": 1.5
}
```

### Network Configuration

**Server Ports**:
- MCP Server: 8001
- Streamlit Client: 8501

**Host Binding**:
- Server: `0.0.0.0:8001` (Docker-compatible)
- Client: `0.0.0.0:8501` (Docker-compatible)

### Docker-Specific Considerations

#### Logo Path Configuration
The logo path is configured as a relative path (`RevealLabs_Logo.png`) to ensure compatibility between local development and Docker containerized deployment:

**Local Development**: Logo file is in the same directory as the Streamlit app
**Docker Container**: Logo file is copied to `/app/` directory during build

The `render_header()` function includes fallback logic to check multiple possible paths:
```python
possible_paths = [
    logo_path,  # Original path from config
    f"/app/{logo_path}",  # Docker container path
    f"./{logo_path}",  # Current directory
    f"../{logo_path}",  # Parent directory
]
```

#### File Structure in Docker
```
/app/
├── streamlit_app.py
├── RevealLabs_Logo.png
├── utils/
│   ├── config.py
│   ├── ui_components.py
│   └── ...
└── requirements.txt
```

### Security Considerations

#### Database Security
- Parameterized queries prevent SQL injection
- Column and table name validation
- Connection timeout protection
- Environment variable configuration

#### API Security
- Input validation and sanitization
- Error message filtering
- Timeout protection
- Resource limits

### Monitoring and Logging

#### Health Checks
- Database connection status
- Query execution monitoring
- Error rate tracking
- Performance metrics

#### Logging Configuration
- Error logging with context
- Performance logging
- Security event logging
- Debug information

---

## Process Flow Diagrams

### Complete System Flow

```
┌─────────────────┐
│   User Input    │
│  (Natural Lang) │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  MCP Client     │
│  (Streamlit)    │
│  + Session ID   │
└─────────┬───────┘
          │ HTTP Request
          │ (session_id)
          ▼
┌─────────────────┐
│  MCP Server     │
│  (FastMCP)      │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Session Memory │
│  (Get Defaults) │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  NLP Intent     │
│  Parser         │
│  (with defaults)│
└─────────┬───────┘
          │ OpenAI API
          │ (GPT-4o-mini)
          ▼
┌─────────────────┐
│  Intent JSON    │
│  + Apply Defaults│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Update Session │
│  Memory         │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Query Builder  │
│  (AIES-specific)│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Database       │
│  Execution      │
│  (with timeout)  │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Result         │
│  Processing     │
│  + SQL Logging  │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Response       │
│  to Client      │
└─────────────────┘
```

### NLP Intent Processing Flow

```
┌─────────────────┐
│  User Query     │
│  "Show data for │
│  enterprise 000"│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Get Default    │
│  Parameters     │
│  (if session)   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  System Prompt  │
│  + Examples     │
│  + Defaults     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  OpenAI API     │
│  (GPT-4o-mini)  │
│  JSON Format    │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  JSON Response  │
│  {              │
│    "action":    │
│    "fetch_data",│
│    "filters": { │
│      "ent_id":  │
│      "000"      │
│    }            │
│  }              │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Apply Defaults │
│  (if missing)   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Update Session │
│  Memory         │
└─────────────────┘
```

### Database Query Execution Flow

```
┌─────────────────┐
│  Intent JSON    │
│  {              │
│    "action":    │
│    "fetch_data",│
│    "filters": { │
│      "ent_id":  │
│      "000"      │
│    }            │
│  }              │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Action         │
│  Routing        │
│  (6 query types)│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Parameter      │
│  Extraction     │
│  - ent_id/name  │
│  - variables    │
│  - dates        │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  SQL            │
│  Construction   │
│  (AIES-specific)│
│  - Base Join    │
│  - Subqueries   │
│  - Parameters   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Database       │
│  Execution      │
│  (60s timeout) │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Result         │
│  Processing     │
│  - Formatting   │
│  - SQL Logging  │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Response       │
│  JSON + SQL     │
└─────────────────┘
```

### Error Handling Flow

```
┌─────────────────┐
│  Operation      │
│  Execution      │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Error          │
│  Occurs?        │
└─────────┬───────┘
          │ Yes
          ▼
┌─────────────────┐
│  Error Type     │
│  Classification │
│  - Validation   │
│  - Database     │
│  - Timeout      │
│  - Parsing      │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Error          │
│  Processing     │
│  - Logging      │
│  - Formatting   │
│  - Context      │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Error          │
│  Response       │
│  {              │
│    "error":     │
│    "message"    │
│  }              │
└─────────────────┘
```

---

## Conclusion

The MCP Server provides a comprehensive natural language interface to database operations through a well-architected system of components. The documentation above covers all major processes, from initial user input through final response delivery, including error handling, security measures, and deployment considerations.

Key strengths of the system include:
- **Domain-Specific Design**: Tailored for enterprise and company data operations in the AIES database
- **Robust NLP Processing**: Sophisticated intent parsing with 6 specialized query types
- **Session-Based Context**: Remembers enterprise ID and company name across queries
- **Secure Database Access**: Parameterized queries prevent SQL injection
- **Complex Join Patterns**: Efficient handling of multi-table joins across schemas
- **Reliable Error Handling**: Comprehensive error classification with SQL query logging
- **Production Ready**: 60-second timeout protection, logging, and containerized deployment

This documentation serves as a complete reference for understanding, maintaining, and extending the MCP server system for AIES database operations.
