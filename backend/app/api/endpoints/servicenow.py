import os
import json
import httpx
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from app.db.neo4j import neo4j_driver
import structlog

from app.models.servicenow import (
    ServiceNowTable, ServiceNowColumn, ServiceNowTableResponse,
    ServiceNowColumnsResponse, ServiceNowRecordsResponse,
    ServiceNowExportRequest, ServiceNowExportResponse, ServiceNowConnectionStatus
)
from app.models.user import User
from app.auth.auth import get_current_active_user

router = APIRouter()
logger = structlog.get_logger()

# ServiceNow credentials
servicenow_url = os.environ.get("SERVICENOW_INSTANCE_URL")
servicenow_username = os.environ.get("SERVICENOW_INSTANCE_USERNAME")
servicenow_password = os.environ.get("SERVICENOW_INSTANCE_PASSWORD")
# Note: Neo4j connection now handled by centralized driver in app.db.neo4j

snow_tables = [
    {"label": "Incident", "name": "incident", "primary": "number"},
    {"label": "Change Request", "name": "change_request", "primary": "number"},
    {"label": "Problem", "name": "problem", "primary": "number"},
    {"label": "User", "name": "sys_user", "primary": "name"},
    {"label": "Group", "name": "sys_user_group", "primary": "name"},
    {"label": "Catalog Item", "name": "sc_cat_item", "primary": "name"},
    {"label": "Catalog Task", "name": "sc_task", "primary": "number"},
    {"label": "Knowledge Base", "name": "kb_knowledge", "primary": "number"},
]


def flatten_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten ServiceNow response dictionary"""
    flattened = {}
    if hasattr(d, 'items'):
        for k, v in d.items():
            if isinstance(v, dict):
                flattened[k] = v.get('display_value', v)
            elif isinstance(v, list):
                flattened[k] = json.dumps(v)
            elif v is not None:
                flattened[k] = v
    return flattened


def get_servicenow_data(tbl: str, qp: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Fetch data from ServiceNow table"""
    if (not servicenow_url or servicenow_url.strip() == "" or 
        not servicenow_username or servicenow_username.strip() == "" or 
        not servicenow_password or servicenow_password.strip() == ""):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ServiceNow credentials not configured"
        )
    
    endpoint = f"{servicenow_url}/api/now/table/{tbl}"
    params = qp or {}
    params['sysparm_limit'] = params.get('sysparm_limit', 10)
    
    try:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        with httpx.Client() as client:
            response = client.get(
                endpoint,
                auth=(servicenow_username, servicenow_password),
                headers=headers,
                params=params,
                timeout=30.0  # Add timeout to prevent hanging
            )
            response.raise_for_status()
            
            # Check if response has content before parsing JSON
            if not response.content:
                logger.warning(f"Empty response from ServiceNow for table {tbl}")
                return []
                
            try:
                response_data = response.json()
                data = response_data.get('result', [])
                logger.info(f"Fetched {len(data)} records from {tbl}")
                return data
            except (ValueError, KeyError) as json_error:
                logger.error(f"Invalid JSON response from ServiceNow for table {tbl}: {json_error}. Response: {response.text[:200]}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Invalid response from ServiceNow: {str(json_error)}"
                )
        
    except httpx.RequestError as e:
        logger.error(f"Error fetching data from ServiceNow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch data from ServiceNow: {str(e)}"
        )


def get_servicenow_tables_safely() -> List[Dict[str, Any]]:
    """Safely fetch ServiceNow tables with fallback to default list"""
    try:
        if (not servicenow_url or servicenow_url.strip() == "" or 
            not servicenow_username or servicenow_username.strip() == "" or 
            not servicenow_password or servicenow_password.strip() == ""):
            logger.warning(f"ServiceNow credentials not configured: URL={bool(servicenow_url and servicenow_url.strip())}, Username={bool(servicenow_username and servicenow_username.strip())}, Password={bool(servicenow_password and servicenow_password.strip())}, using default tables")
            return snow_tables
            
        # Fetch commonly used tables from ServiceNow
        params = {
            'sysparm_limit': 100,
            'sysparm_fields': 'name,label,super_class',
            'sysparm_query': 'super_class.name=task^ORname=sys_user^ORname=sys_user_group^ORname=sc_cat_item^ORname=kb_knowledge^ORname=cmdb_ci'
        }
        
        url = f"{servicenow_url}/api/now/table/sys_db_object"
        logger.info(f"Fetching ServiceNow tables from: {url}")
        
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        with httpx.Client() as client:
            response = client.get(
                url,
                auth=(servicenow_username, servicenow_password),
                headers=headers,
                params=params,
                timeout=30.0
            )
            logger.info(f"ServiceNow response: Status={response.status_code}, Content-Type={response.headers.get('content-type', 'unknown')}, Content-Length={len(response.content)}")
            response.raise_for_status()
        
        # Check if response has content before parsing JSON
        if not response.content:
            logger.warning("Empty response from ServiceNow, using default tables")
            return snow_tables
            
        try:
            response_data = response.json()
            tables_data = response_data.get('result', [])
        except (ValueError, KeyError) as json_error:
            logger.warning(f"Invalid JSON response from ServiceNow: {json_error}. Response status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}, Response content: {response.text[:200]}")
            return snow_tables
        servicenow_tables = []
        
        for table_record in tables_data:
            flat_record = flatten_dict(table_record)
            name = flat_record.get('name', '')
            label = flat_record.get('label', name)
            
            # Determine primary key based on table type
            if name in ['incident', 'change_request', 'problem', 'sc_task']:
                primary = 'number'
            elif name in ['sys_user', 'sys_user_group', 'sc_cat_item', 'kb_knowledge']:
                primary = 'name'
            else:
                primary = 'sys_id'
            
            if name and label:
                servicenow_tables.append({
                    'name': name,
                    'label': label,
                    'primary': primary
                })
        
        if servicenow_tables:
            logger.info(f"Fetched {len(servicenow_tables)} tables from ServiceNow instance")
            return servicenow_tables
        else:
            logger.warning("No tables found from ServiceNow, using default table list")
            return snow_tables
            
    except Exception as e:
        logger.warning(f"Failed to fetch tables from ServiceNow: {e}, using default tables")
        return snow_tables


async def create_neo4j_nodes_relationships(data: List[Dict[str, Any]], refs: List[Dict[str, Any]], node_label: str, unique_key: str) -> int:
    """Create nodes and relationships in Neo4j using the async driver"""
    created_count = 0
    
    try:
        # Use the existing async Neo4j driver with rate limiting protection
        await neo4j_driver.connect()
        
        for row in data:
            try:
                flat_row = flatten_dict(row)
                unique_id = flat_row.get('sys_id')
                if not unique_id:
                    logger.warning(f"Skipping row without sys_id: {row}")
                    continue
                
                # Ensure unique_key value exists
                unique_value = flat_row.get(unique_key)
                if not unique_value:
                    logger.warning(f"Skipping row without {unique_key}: {unique_id}")
                    continue
                
                cypher = f"""
                MERGE (n:{node_label.upper()} {{`{unique_key}`: $unique_id}})
                SET n += $properties
                """
                # Process references
                for attr, val in row.items():
                    try:
                        # Skip if val is None or empty
                        if not val:
                            continue
                            
                        # Find reference definition for this attribute
                        ref = [tup for tup in refs if tup.get('element') == attr]
                        
                        # Check if ref list is not empty and has reference type
                        if ref and len(ref) > 0:
                            ref_dict = ref[0]
                            internal_type = ref_dict.get('internal_type', {})
                            
                            # Safely check if it's a reference type
                            if isinstance(internal_type, dict) and internal_type.get('value') == 'reference':
                                # Extract reference information safely
                                if isinstance(val, dict):
                                    ref_node = val.get('display_value')
                                else:
                                    ref_node = str(val)
                                
                                reference_info = ref_dict.get('reference', {})
                                if isinstance(reference_info, dict):
                                    ref_node_label = reference_info.get('value', '').upper()
                                else:
                                    ref_node_label = str(reference_info).upper()
                                
                                relationship_name = attr.upper()
                                
                                # Only add relationship if we have valid reference data
                                if ref_node_label and ref_node and ref_node_label != 'NONE':
                                    # Escape single quotes in ref_node to prevent Cypher injection
                                    ref_node_escaped = ref_node.replace("'", "\\'")
                                    cypher += f"""
                        MERGE ({attr}:{ref_node_label} {{`name`: '{ref_node_escaped}'}})
                        MERGE (n)-[:{relationship_name}]->({attr})
                        """
                    except (KeyError, AttributeError, TypeError) as ref_error:
                        logger.warning(f"Error processing reference {attr}: {ref_error}")
                        continue
                # Use execute_write for write operations
                await neo4j_driver.execute_query(cypher, {
                    'unique_id': unique_value,
                    'properties': flat_row
                })
                created_count += 1
                
            except Exception as e:
                logger.error(f"Error creating node for {row.get(unique_key, 'unknown')}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Neo4j operation error: {e}")
        # Check if it's an authentication rate limit error
        if "authentication rate limit" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Neo4j authentication rate limit exceeded. Please wait before retrying."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Neo4j nodes: {str(e)}"
        )
    
    return created_count


@router.get("/connection-status", response_model=ServiceNowConnectionStatus)
async def get_servicenow_connection_status(
    current_user: User = Depends(get_current_active_user)
):
    """Check ServiceNow connection status"""
    try:
        logger.info(f"Checking ServiceNow connection with URL: {servicenow_url or 'Not configured'}")
        
        # Check for missing credentials with detailed messaging
        missing_creds = []
        if not servicenow_url or servicenow_url.strip() == "":
            missing_creds.append("SERVICENOW_INSTANCE_URL")
        if not servicenow_username or servicenow_username.strip() == "":
            missing_creds.append("SERVICENOW_INSTANCE_USERNAME") 
        if not servicenow_password or servicenow_password.strip() == "":
            missing_creds.append("SERVICENOW_INSTANCE_PASSWORD")
            
        if missing_creds:
            missing_str = ", ".join(missing_creds)
            logger.warning(f"ServiceNow credentials not configured. Missing: {missing_str}")
            return ServiceNowConnectionStatus(
                connected=False,
                message=f"ServiceNow credentials not configured. Missing environment variables: {missing_str}"
            )
        
        # Test connection with a simple query
        url = f"{servicenow_url}/api/now/table/sys_db_object"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        logger.info(f"Testing ServiceNow connection to: {url}")
        
        with httpx.Client() as client:
            response = client.get(
                url,
                auth=(servicenow_username, servicenow_password),
                headers=headers,
                params={'sysparm_limit': 1},
                timeout=10.0
            )
            
        logger.info(f"ServiceNow response: Status={response.status_code}, Content-Type={response.headers.get('content-type', 'unknown')}, Content-Length={len(response.content)}")
        
        if response.status_code == 200:
            # Verify we get valid JSON response
            try:
                if response.content:
                    logger.info(f"ServiceNow response content sample: {response.text[:1000]}")
                    json_data = response.json()  # Just test if it's valid JSON
                    logger.info(f"JSON parsing successful. Response keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dict'}")
                    connection_valid = True
                else:
                    logger.warning("ServiceNow returned empty response")
                    connection_valid = False
            except (ValueError, KeyError) as json_error:
                logger.error(f"ServiceNow returned invalid JSON: {json_error}")
                logger.error(f"Response headers: {dict(response.headers)}")
                logger.error(f"Full response content: {response.text}")
                connection_valid = False
                
            if connection_valid:
                # Get actual table count
                servicenow_tables = get_servicenow_tables_safely()
                return ServiceNowConnectionStatus(
                    connected=True,
                    message="Successfully connected to ServiceNow",
                    instance_url=servicenow_url,
                    tables_count=len(servicenow_tables)
                )
            else:
                return ServiceNowConnectionStatus(
                    connected=False,
                    message="ServiceNow connection failed: Invalid response format"
                )
        else:
            # Log response details for debugging
            logger.warning(f"ServiceNow connection failed: HTTP {response.status_code}")
            logger.warning(f"Response content (first 500 chars): {response.text[:500]}")
            return ServiceNowConnectionStatus(
                connected=False,
                message=f"ServiceNow connection failed: HTTP {response.status_code}"
            )
            
    except Exception as e:
        logger.error(f"ServiceNow connection test failed: {e}")
        return ServiceNowConnectionStatus(
            connected=False,
            message=f"ServiceNow connection failed: {str(e)}"
        )


@router.get("/tables", response_model=ServiceNowTableResponse)
async def get_servicenow_tables(
    current_user: User = Depends(get_current_active_user)
):
    """Get available ServiceNow tables from the connected instance"""
    try:
        # Fetch tables from ServiceNow instance with fallback
        servicenow_tables = get_servicenow_tables_safely()
        tables = [ServiceNowTable(**table) for table in servicenow_tables]
        
        return ServiceNowTableResponse(tables=tables)
    except Exception as e:
        logger.error(f"Error processing ServiceNow tables: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch ServiceNow tables"
        )


@router.get("/columns", response_model=ServiceNowColumnsResponse)
async def get_servicenow_table_columns(
    table: str = Query(..., description="ServiceNow table name"),
    current_user: User = Depends(get_current_active_user)
):
    """Get columns for a specific ServiceNow table"""
    try:
        params = {
            'sysparm_limit': 1000,
            'sysparm_query': f"name={table}^ORname=task",
            'sysparm_fields': "element,column_label"
        }
        
        data = get_servicenow_data("sys_dictionary", params)
        flattened_data = [flatten_dict(record) for record in data]
        
        columns = []
        for record in flattened_data:
            if record.get('element') and record.get('column_label'):
                columns.append(ServiceNowColumn(
                    element=record['element'],
                    column_label=record['column_label']
                ))
        
        return ServiceNowColumnsResponse(columns=columns)
    
    except Exception as e:
        logger.error(f"Error fetching ServiceNow table columns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch ServiceNow table columns"
        )


@router.get("/records", response_model=ServiceNowRecordsResponse)
async def get_servicenow_table_records(
    table: str = Query(..., description="ServiceNow table name"),
    page: int = Query(1, description="Page number"),
    size: int = Query(10, description="Page size"),
    sort_field: Optional[str] = Query(None, description="Sort field"),
    sort_order: Optional[str] = Query("asc", description="Sort order (asc/desc)"),
    filters: Optional[str] = Query(None, description="ServiceNow query filters"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields"),
    current_user: User = Depends(get_current_active_user)
):
    """Get records from a ServiceNow table"""
    try:
        params = {
            'sysparm_limit': size,
            'sysparm_offset': (page - 1) * size,
            'sysparm_display_value': 'all'
        }
        
        if sort_field:
            if sort_order == 'desc':
                params['sysparm_order_by'] = f"{sort_field}^DESC"
            else:
                params['sysparm_order_by'] = sort_field
        
        if filters:
            params['sysparm_query'] = filters
        
        if fields:
            params['sysparm_fields'] = fields
        
        data = get_servicenow_data(table, params)
        flattened_data = [flatten_dict(record) for record in data]
        
        return ServiceNowRecordsResponse(
            records=flattened_data,
            total=len(flattened_data),
            page=page,
            size=size
        )
    
    except Exception as e:
        logger.error(f"Error fetching ServiceNow table records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch ServiceNow table records"
        )


@router.post("/export", response_model=ServiceNowExportResponse)
async def export_servicenow_table(
    export_request: ServiceNowExportRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Export ServiceNow table data to Neo4j"""
    try:
        # Get table schema for reference columns
        schema_params = {
            'sysparm_limit': 10000,
            'sysparm_query': f"name={export_request.table}^ORname=task",
            'sysparm_fields': "element,internal_type,reference"
        }
        
        sys_dicts = get_servicenow_data("sys_dictionary", schema_params)
        
        # Get actual data
        data_params = {
            'sysparm_limit': export_request.limit,
            'sysparm_display_value': 'all'
        }
        
        if export_request.filters:
            data_params['sysparm_query'] = export_request.filters
        
        if export_request.fields:
            data_params['sysparm_fields'] = f"sys_id,{export_request.fields}"
        
        data = get_servicenow_data(export_request.table, data_params)
        
        # Create Neo4j nodes
        created_count = await create_neo4j_nodes_relationships(
            data,
            sys_dicts,
            node_label=export_request.table,
            unique_key='sys_id'
        )
        
        return ServiceNowExportResponse(
            message=f"Successfully exported {created_count} records from {export_request.table}",
            exported_count=created_count,
            table_name=export_request.table
        )
    
    except Exception as e:
        logger.error(f"Error exporting ServiceNow table: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export ServiceNow table data"
        )


@router.get("/debug-connection")
async def debug_servicenow_connection(
    current_user: User = Depends(get_current_active_user)
):
    """Debug endpoint to test ServiceNow connection with detailed response info"""
    try:
        logger.info("=== ServiceNow Debug Connection Test ===")
        
        # Check credentials
        if (not servicenow_url or servicenow_url.strip() == "" or 
            not servicenow_username or servicenow_username.strip() == "" or 
            not servicenow_password or servicenow_password.strip() == ""):
            return {
                "status": "error",
                "message": "ServiceNow credentials not configured",
                "url_configured": bool(servicenow_url and servicenow_url.strip()),
                "username_configured": bool(servicenow_username and servicenow_username.strip()),
                "password_configured": bool(servicenow_password and servicenow_password.strip())
            }
        
        # Test connection with basic authentication
        url = f"{servicenow_url}/api/now/table/sys_db_object"
        
        # Try different header configurations that ServiceNow might expect
        headers_v1 = {"Accept": "application/json"}
        headers_v2 = {"Content-Type": "application/json", "Accept": "application/json"}
        
        params = {'sysparm_limit': 1}
        
        logger.info(f"Making request to: {url}")
        logger.info(f"Username: {servicenow_username}")
        logger.info(f"Params: {params}")
        
        # Try the connection with minimal headers first
        with httpx.Client() as client:
            response = client.get(
                url,
                auth=(servicenow_username, servicenow_password),
                headers=headers_v1,
                params=params,
                timeout=30.0
            )
        
        # Detailed response analysis
        result = {
            "status": "success" if response.status_code == 200 else "error",
            "http_status": response.status_code,
            "content_type": response.headers.get('content-type', 'unknown'),
            "content_length": len(response.content),
            "response_headers": dict(response.headers),
            "response_text_sample": response.text[:500] if response.content else "EMPTY",
        }
        
        # Try to parse JSON
        if response.content:
            try:
                json_data = response.json()
                result["json_valid"] = True
                result["json_keys"] = list(json_data.keys()) if isinstance(json_data, dict) else "Not a dict"
                if isinstance(json_data, dict) and 'result' in json_data:
                    result["result_count"] = len(json_data['result'])
            except Exception as json_error:
                result["json_valid"] = False
                result["json_error"] = str(json_error)
        else:
            result["json_valid"] = False
            result["json_error"] = "Empty response"
        
        logger.info(f"Debug result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Debug connection failed: {e}")
        return {
            "status": "error",
            "message": f"Connection failed: {str(e)}",
            "error_type": type(e).__name__
        }


@router.post("/reset-neo4j-connection")
async def reset_neo4j_connection(
    current_user = Depends(get_current_active_user)
):
    """Reset Neo4j connection state to recover from rate limiting"""
    try:
        await neo4j_driver.reset_connection()
        return {"message": "Neo4j connection reset successfully"}
    except Exception as e:
        logger.error(f"Failed to reset Neo4j connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset connection: {str(e)}"
        )
