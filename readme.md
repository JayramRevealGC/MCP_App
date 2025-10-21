# MCP Server Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [NLP Intent Processing](#nlp-intent-processing)
3. [Database Layer Components](#database-layer-components)
4. [Query Execution Process](#query-execution-process)
5. [MCP API Endpoints](#mcp-api-endpoints)
6. [Error Handling & Timeout Management](#error-handling--timeout-management)
7. [Deployment & Configuration](#deployment--configuration)
8. [Process Flow Diagrams](#process-flow-diagrams)

---

## Architecture Overview

The MCP (Model Context Protocol) Server is a sophisticated natural language to database query system that enables users to interact with databases using conversational language. The system is built using FastMCP and provides a RESTful API interface for database operations.

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

1. **Presentation Layer**: Streamlit-based web interface
2. **API Layer**: FastMCP server with HTTP transport
3. **Processing Layer**: NLP intent parsing and query building
4. **Data Access Layer**: Database connection and execution
5. **Storage Layer**: PostgreSQL database

### Key Features

- **Natural Language Processing**: Converts user queries into structured database operations
- **Multiple Query Types**: Supports tables, records, joins, unions, summaries, and analytics
- **Advanced Filtering**: Complex WHERE conditions with multiple operators
- **Data Visualization**: Built-in support for charts and graphs
- **Timeout Protection**: Prevents long-running queries from blocking the system
- **Error Handling**: Comprehensive validation and error reporting

---

## NLP Intent Processing

### Overview

The NLP intent processing system converts natural language queries into structured JSON intents that can be executed against the database. This process uses OpenAI's GPT-4o-mini model to understand user intent and map it to specific database operations.

### Process Flow

```
User Query → OpenAI API → Intent JSON → Database Action → Results
```

### Intent Parser (`nlp_intent.py`)

**Function**: `parse_nl_to_intent(user_input: str) -> dict`

**Process**:
1. **Input Processing**: Receives natural language query from user
2. **System Prompt**: Uses comprehensive prompt with examples for all supported operations
3. **AI Processing**: Sends query to OpenAI GPT-4o-mini model
4. **Response Parsing**: Converts AI response to structured JSON
5. **Error Handling**: Returns fallback intent if parsing fails

**Supported Operations**:

| Operation | Description | Example Query |
|-----------|-------------|---------------|
| `fetch_tables` | List all available tables | "Show me all tables" |
| `fetch_n_records` | Get records from single table | "Get 5 users where age > 25" |
| `fetch_n_joined_records` | Join two tables | "Join users and orders" |
| `fetch_n_appended_records` | Union two tables | "Combine users and customers" |
| `get_table_summary` | Table metadata and stats | "Summary of products table" |
| `summarize_column` | Column value distribution | "Count values in status column" |
| `analyze_relationship` | Categorical vs quantitative analysis | "Revenue by category" |

### Intent Structure

```json
{
    "action": "fetch_n_records",
    "filters": {
        "table_name": "users",
        "n": 5,
        "columns": ["id", "name", "email"],
        "condition": {
            "column": "age",
            "operator": ">",
            "value": 25
        },
        "order_by": {
            "column": "name",
            "direction": "ASC"
        }
    }
}
```

### Supported Operators

- **Comparison**: `=`, `>`, `<`, `>=`, `<=`, `!=`
- **Pattern Matching**: `LIKE`, `ILIKE`
- **Range**: `BETWEEN`
- **Set Membership**: `IN`
- **Null Checks**: `IS NULL`, `IS NOT NULL`

### Advanced Features

- **Table Prefixes**: Support for `table.column` syntax in joins
- **Flexible Joins**: INNER, LEFT, RIGHT, FULL OUTER joins
- **Dynamic Columns**: Automatic column detection and validation
- **Ordering**: ASC/DESC sorting on any column
- **Limits**: Configurable result set sizes

---

## Database Layer Components

### Overview

The database layer provides a robust, secure, and efficient interface to PostgreSQL databases. It consists of multiple specialized modules working together to handle database operations safely.

### Component Architecture

```
┌─────────────────┐
│   Executor      │ ← Main execution coordinator
├─────────────────┤
│   Query Builder │ ← SQL construction
├─────────────────┤
│   Validation    │ ← Input validation
├─────────────────┤
│   Connection    │ ← Database connectivity
└─────────────────┘
```

### 1. Connection Management (`connection.py`)

**Purpose**: Handles database connections and timeout management

**Key Functions**:
- `get_connection()`: Establishes PostgreSQL connection using environment variables
- `execute_with_timeout()`: Executes functions with 30-second timeout protection
- `QueryTimeoutError`: Custom exception for timeout scenarios

**Configuration**:
```python
QUERY_TIMEOUT = 30  # seconds
```

**Environment Variables**:
- `PG_HOST`: Database host
- `PG_PORT`: Database port
- `PG_USER`: Database username
- `PG_PASSWORD`: Database password
- `PG_DATABASE`: Database name

### 2. Query Builder (`query_builder.py`)

**Purpose**: Constructs SQL queries from structured intents

**Key Functions**:
- `format_columns_for_sql()`: Formats column lists for SELECT statements
- `format_join_condition()`: Creates JOIN conditions
- `ACTION_SQL_MAP`: Maps actions to SQL templates

**SQL Templates**:
```python
ACTION_SQL_MAP = {
    "fetch_tables": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'space_product_aies';",
    "fetch_n_records": "SELECT {} FROM space_product_aies.{}{}{} LIMIT %s;",
    "fetch_n_joined_records": "SELECT {} FROM space_product_aies.{} {} JOIN space_product_aies.{} ON {}{}{} LIMIT %s;",
    "fetch_n_appended_records": "SELECT {} FROM space_product_aies.{}{} UNION ALL SELECT {} FROM space_product_aies.{}{}{} LIMIT %s;",
    "get_table_summary": "SELECT COUNT(*) as row_count FROM space_product_aies.{};",
    "summarize_column": "SELECT {}, COUNT(*) as count FROM space_product_aies.{} GROUP BY {} ORDER BY count DESC;",
    "analyze_relationship": "SELECT {} as {}, SUM({}) as {} FROM space_product_aies.{} GROUP BY {} ORDER BY {} DESC;"
}
```

### 3. Validation (`validation.py`)

**Purpose**: Validates database inputs to prevent SQL injection and ensure data integrity

**Key Functions**:

#### `validate_columns(table_name, columns)`
- Validates column existence in specified table
- Returns all columns if validation fails
- Prevents SQL injection through column name validation

#### `validate_join_columns(table1, table2, join_columns)`
- Validates join column existence in both tables
- Returns validated column names
- Raises ValueError for invalid columns

#### `validate_join_type(join_type)`
- Validates and normalizes join types
- Supported: INNER, LEFT, RIGHT, FULL, FULL OUTER
- Returns uppercase normalized type

#### `validate_order_by(table_name, order_by)`
- Validates ORDER BY clauses
- Checks column existence and sort direction
- Supports table-prefixed column names

#### `parse_condition(condition, table_name)`
- Parses flexible condition dictionaries
- Supports all SQL operators
- Returns SQL WHERE clause and parameters
- Prevents SQL injection through parameterized queries

**Security Features**:
- Column name validation against database schema
- Parameterized queries for all user inputs
- Table name validation
- Operator whitelisting

---

## Query Execution Process

### Overview

The query execution process coordinates all database operations, from intent parsing to result delivery. It ensures security, performance, and reliability through comprehensive validation and error handling.

### Execution Flow

```
Intent → Validation → SQL Construction → Execution → Result Processing → Response
```

### Main Executor (`executor.py`)

**Function**: `execute_action(action: str, filters: dict)`

**Process Steps**:

1. **Connection Establishment**
   - Creates database connection using `get_connection()`
   - Sets up cursor with dictionary row factory
   - Implements connection cleanup in finally block

2. **Action Routing**
   - Routes to appropriate handler based on action type
   - Each action has specialized processing logic

3. **Query Execution**
   - Constructs SQL using query builder
   - Executes with timeout protection
   - Handles result processing

4. **Error Handling**
   - Catches and formats database errors
   - Returns structured error responses
   - Implements timeout protection

### Action-Specific Processing

#### 1. Fetch Tables (`fetch_tables`)
```python
sql = ACTION_SQL_MAP[action]
cur.execute(sql)
rows = cur.fetchall()
return [dict(row) for row in rows]
```

#### 2. Fetch Records (`fetch_n_records`)
**Process**:
1. Extract table name, limit, and columns from filters
2. Parse conditions (WHERE clause)
3. Parse ordering (ORDER BY clause)
4. Validate columns against database schema
5. Construct parameterized SQL query
6. Execute with condition parameters and limit
7. Return formatted results

**Features**:
- Dynamic column selection
- Complex WHERE conditions
- Flexible ordering
- Configurable limits

#### 3. Join Records (`fetch_n_joined_records`)
**Process**:
1. Validate table names and join columns
2. Determine join type (INNER, LEFT, RIGHT, FULL OUTER)
3. Handle table-prefixed column names
4. Parse conditions and ordering
5. Construct JOIN query with proper aliasing
6. Execute and return results

**Advanced Features**:
- Flexible join column mapping
- Table prefix resolution
- Cross-table condition support
- Automatic column prefixing

#### 4. Append Records (`fetch_n_appended_records`)
**Process**:
1. Validate table names
2. Find common columns between tables
3. Parse conditions and ordering
4. Construct UNION ALL query
5. Execute with proper column alignment
6. Return combined results

**Features**:
- Automatic common column detection
- Column alignment validation
- Cross-table condition support

#### 5. Table Summary (`get_table_summary`)
**Process**:
1. Get row count using COUNT(*)
2. Retrieve column information from information_schema
3. Fetch sample data (first 3 rows)
4. Return comprehensive table metadata

**Returns**:
- Table name
- Row count
- Column count and names
- Sample data rows

#### 6. Column Summary (`summarize_column`)
**Process**:
1. Validate column existence
2. Execute GROUP BY query with COUNT
3. Create visualization configuration
4. Return data and chart metadata

**Visualization Support**:
- Bar chart configuration
- Title and field mapping
- Data formatting for frontend

#### 7. Relationship Analysis (`analyze_relationship`)
**Process**:
1. Validate categorical and quantitative columns
2. Execute GROUP BY with SUM aggregation
3. Create histogram visualization configuration
4. Return analysis data and chart metadata

**Features**:
- Categorical vs quantitative analysis
- Histogram visualization support
- Statistical aggregation

### Timeout Protection

**Implementation**:
- 30-second query timeout using threading
- `execute_with_timeout()` wrapper function
- `QueryTimeoutError` exception handling
- Graceful timeout response

**Benefits**:
- Prevents system blocking
- Protects against runaway queries
- Maintains system responsiveness

---

## MCP API Endpoints

### Overview

The MCP server exposes a single tool endpoint that handles all database operations through natural language processing.

### API Structure

**Base URL**: `http://host:8001/mcp`
**Transport**: Streamable HTTP
**Protocol**: Model Context Protocol (MCP)

### Available Tools

#### `query_users(user_query: str) -> dict`

**Description**: Main entry point for all database operations

**Parameters**:
- `user_query` (str): Natural language query describing the desired database operation

**Returns**:
```json
{
    "result": [
        // Array of database results or error objects
    ]
}
```

**Process Flow**:
1. **Intent Parsing**: Convert natural language to structured intent
2. **Action Execution**: Execute database operation based on intent
3. **Result Formatting**: Return structured results

**Example Usage**:
```python
# List all tables
result = await query_users("Show me all tables")

# Get specific records
result = await query_users("Get 5 users where age > 25")

# Join tables
result = await query_users("Join users and orders on user_id")

# Analyze data
result = await query_users("Show revenue by category")
```

### Server Configuration

**Core Setup** (`core.py`):
```python
mcp = FastMCP("nlp-db-server", host="0.0.0.0", port=8001)
```

**Tool Registration** (`tools.py`):
```python
@mcp.tool()
async def query_users(user_query: str) -> dict:
    intent = await parse_nl_to_intent(user_query)
    result = execute_action(intent["action"], intent.get("filters", {}))
    return {"result": result}
```

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
**Threshold**: 30 seconds
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

**Handling**:
```python
try:
    return json.loads(intent_text)
except Exception:
    return {"action": "unknown", "filters": {}}
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
    "All the tables in the database",
    "10 random rows from the table item_kaus",
    "Row with id 1957777 from the table item_kaus",
    "7 joined records from the table item_kaus_original and item_kaus"
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
```

### Network Configuration

**Server Ports**:
- MCP Server: 8001
- Streamlit Client: 8501

**Host Binding**:
- Server: `0.0.0.0:8001` (Docker-compatible)
- Client: `0.0.0.0:8501` (Docker-compatible)

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
└─────────┬───────┘
          │ HTTP Request
          ▼
┌─────────────────┐
│  MCP Server     │
│  (FastMCP)      │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  NLP Intent     │
│  Parser         │
└─────────┬───────┘
          │ OpenAI API
          ▼
┌─────────────────┐
│  Intent JSON    │
│  Processing     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Query Builder  │
│  & Validation   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Database       │
│  Execution      │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Result         │
│  Processing     │
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
│  "Get 5 users   │
│  where age>25"  │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  System Prompt  │
│  + Examples     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  OpenAI API     │
│  (GPT-4o-mini)  │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  JSON Response  │
│  {              │
│    "action":    │
│    "fetch_n_    │
│    records",    │
│    "filters":    │
│    {...}        │
│  }              │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Intent         │
│  Validation     │
└─────────────────┘
```

### Database Query Execution Flow

```
┌─────────────────┐
│  Intent JSON    │
│  {              │
│    "action":    │
│    "fetch_n_    │
│    records",    │
│    "filters":    │
│    {...}        │
│  }              │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Action         │
│  Routing        │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Input          │
│  Validation     │
│  - Columns      │
│  - Tables       │
│  - Conditions   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  SQL            │
│  Construction   │
│  - Templates    │
│  - Parameters   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Database       │
│  Execution      │
│  (with timeout) │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Result         │
│  Processing     │
│  - Formatting   │
│  - Visualization│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Response       │
│  JSON           │
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
- **Robust NLP Processing**: Sophisticated intent parsing with comprehensive examples
- **Secure Database Access**: Multiple layers of validation and parameterized queries
- **Flexible Query Support**: Support for complex operations including joins, unions, and analytics
- **Reliable Error Handling**: Comprehensive error classification and user-friendly responses
- **Production Ready**: Timeout protection, logging, and containerized deployment

This documentation serves as a complete reference for understanding, maintaining, and extending the MCP server system.
