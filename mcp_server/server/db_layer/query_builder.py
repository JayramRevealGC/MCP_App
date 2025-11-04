"""
SQL query construction for AIES database queries.
Supports 6 specific query patterns for enterprise and company data.
"""

# Base SQL template for the common join pattern used in most queries
BASE_JOIN_PATTERN = """
SELECT {select_columns}
FROM space_meta.units a
INNER JOIN space_meta.product_refper_units b ON a.sscid = b.sscid
INNER JOIN space_meta.product_refpers c ON b.product_refper_id = c.id
INNER JOIN space_meta.products d ON d.id = c.product_id
INNER JOIN space_meta.refpers e ON e.id = c.refper_id
INNER JOIN space_product_aies.control_estabs f ON f.product_refper_unit_id = b.id
INNER JOIN space_product_aies.item_estabs g ON g.product_refper_unit_id = b.id
WHERE d.name = 'AIES'
  AND e.name = '2023'
  {additional_conditions}
"""

# Subquery pattern for company name filtering
COMPANY_SUBQUERY_PATTERN = """
AND a.login_id IN (
    SELECT a.login_id
    FROM space_meta.units a
    INNER JOIN space_meta.product_refper_units b ON b.sscid = a.sscid AND b.login_id = a.login_id
    INNER JOIN space_meta.product_refpers c ON b.product_refper_id = c.id
    INNER JOIN space_meta.products d ON d.id = c.product_id
    INNER JOIN space_meta.refpers e ON e.id = c.refper_id
    INNER JOIN space_product_aies.control_contacts f ON f.product_refper_unit_id = b.id
    WHERE f.mail_addr_name1_txt = %s
)
"""

# Query for getting company name (different join pattern)
GET_COMPANY_NAME_QUERY = """
SELECT f.mail_addr_name1_txt
FROM space_meta.units a
INNER JOIN space_meta.product_refper_units b ON b.sscid = a.sscid AND b.login_id = a.login_id
INNER JOIN space_meta.product_refpers c ON b.product_refper_id = c.id
INNER JOIN space_meta.products d ON d.id = c.product_id
INNER JOIN space_meta.refpers e ON e.id = c.refper_id
INNER JOIN space_product_aies.control_contacts f ON f.product_refper_unit_id = b.id
WHERE a.ent_id = %s
"""

def build_fetch_data_query(variables: list = None, company_name: str = None, ent_id: str = None) -> tuple:
    """
    Unified query builder for fetching data by enterprise ID or company name.
    If specific variables are provided, fetch only those; otherwise fetch all fields.
    Prioritizes ent_id over company_name if both are provided.
    
    Args:
        variables: Optional list of column/variable names to fetch. If None or empty, fetches all fields.
        company_name: Optional company name filter
        ent_id: Optional enterprise ID filter (takes precedence over company_name)
    
    Returns: (sql_query, parameters_list)
    """
    # Determine select columns
    if variables and len(variables) > 0:
        # Fetch specific variables
        select_columns = ", ".join(variables)
    else:
        # Fetch all fields
        select_columns = "a.reporting_id, a.kau_id, a.login_id, a.ent_id, f.*, g.*"
    
    # Determine filter condition (prioritize ent_id)
    parameters = []
    if ent_id:
        additional_conditions = "AND a.ent_id = %s"
        parameters.append(ent_id)
    elif company_name:
        additional_conditions = "\n" + COMPANY_SUBQUERY_PATTERN.strip()
        parameters.append(company_name)
    else:
        additional_conditions = ""
    
    sql = BASE_JOIN_PATTERN.format(
        select_columns=select_columns,
        additional_conditions=additional_conditions
    )
    return sql, parameters

# Legacy functions kept for backward compatibility (deprecated)
def build_fetch_by_ent_id_query(ent_id: str) -> tuple:
    """
    [DEPRECATED] Use build_fetch_data_query instead.
    Build query for fetching all records by enterprise ID.
    
    Returns: (sql_query, parameters_list)
    """
    return build_fetch_data_query(variables=None, ent_id=ent_id)

def build_fetch_by_company_query(company_name: str) -> tuple:
    """
    [DEPRECATED] Use build_fetch_data_query instead.
    Build query for fetching all records by company name.
    
    Returns: (sql_query, parameters_list)
    """
    return build_fetch_data_query(variables=None, company_name=company_name)

def build_get_variables_query(variables: list, company_name: str = None, ent_id: str = None) -> tuple:
    """
    [DEPRECATED] Use build_fetch_data_query instead.
    Build query for getting specific variable values.
    
    Returns: (sql_query, parameters_list)
    """
    return build_fetch_data_query(variables=variables, company_name=company_name, ent_id=ent_id)

def build_compare_variables_query(variable_x: str, variable_y: str, percentage_threshold: float,
                                   company_name: str = None, ent_id: str = None) -> tuple:
    """
    Build query for comparing two variables with percentage difference threshold.
    
    Returns: (sql_query, parameters_list)
    """
    select_columns = f"{variable_x}, {variable_y}"
    parameters = []
    
    # Build additional conditions
    comparison_condition = f"AND ABS({variable_x} - {variable_y}) / NULLIF({variable_y}, 0) > %s"
    parameters.append(percentage_threshold)
    
    if company_name:
        additional_conditions = "\n" + COMPANY_SUBQUERY_PATTERN.strip() + "\n" + comparison_condition
        parameters.insert(0, company_name)
    elif ent_id:
        additional_conditions = f"AND a.ent_id = %s\n{comparison_condition}"
        parameters.insert(0, ent_id)
    else:
        additional_conditions = comparison_condition
    
    sql = BASE_JOIN_PATTERN.format(
        select_columns=select_columns,
        additional_conditions=additional_conditions
    )
    return sql, parameters

def build_filter_by_date_query(submit_date: str) -> tuple:
    """
    Build query for filtering companies by submit date.
    
    Returns: (sql_query, parameters_list)
    """
    select_columns = "a.ent_id"
    date_subquery = """
AND a.login_id IN (
    SELECT a.login_id
    FROM space_meta.units a
    INNER JOIN space_meta.product_refper_units b ON b.sscid = a.sscid AND b.login_id = a.login_id
    INNER JOIN space_meta.product_refpers c ON b.product_refper_id = c.id
    INNER JOIN space_meta.products d ON d.id = c.product_id
    INNER JOIN space_meta.refpers e ON e.id = c.refper_id
    INNER JOIN space_product_aies.control_contacts f ON f.product_refper_unit_id = b.id
    WHERE f.submit_date = %s
)
"""
    additional_conditions = date_subquery.strip()
    sql = BASE_JOIN_PATTERN.format(
        select_columns=select_columns,
        additional_conditions=additional_conditions
    )
    return sql, [submit_date]

def build_count_units_kaus_query(company_name: str = None, ent_id: str = None) -> tuple:
    """
    Build query for counting units and KAUs for a company or enterprise.
    Prioritizes ent_id over company_name if both are provided.
    
    Args:
        company_name: Optional company name filter
        ent_id: Optional enterprise ID filter (takes precedence over company_name)
    
    Returns: (sql_query, parameters_list)
    """
    select_columns = "COUNT(DISTINCT a.reporting_id) as Reporting_IDs, COUNT(DISTINCT a.kau_id) as KAUs"
    
    # Determine filter condition (prioritize ent_id)
    parameters = []
    if ent_id:
        additional_conditions = "AND a.ent_id = %s"
        parameters.append(ent_id)
    elif company_name:
        additional_conditions = "\n" + COMPANY_SUBQUERY_PATTERN.strip()
        parameters.append(company_name)
    else:
        # If neither is provided, this will return an error, but we'll handle it in executor
        additional_conditions = ""
    
    sql = BASE_JOIN_PATTERN.format(
        select_columns=select_columns,
        additional_conditions=additional_conditions
    )
    return sql, parameters

def build_count_enterprises_query() -> tuple:
    """
    Build query for counting unique enterprises.
    
    Returns: (sql_query, parameters_list)
    """
    select_columns = "COUNT(DISTINCT a.ent_id) as Enterprises"
    additional_conditions = ""
    sql = BASE_JOIN_PATTERN.format(
        select_columns=select_columns,
        additional_conditions=additional_conditions
    )
    return sql, []

def build_get_company_name_query(ent_id: str) -> tuple:
    """
    Build query for getting company name from enterprise ID.
    
    Returns: (sql_query, parameters_list)
    """
    return GET_COMPANY_NAME_QUERY.strip(), [ent_id]
