import os
import json
import requests
from neo4j import GraphDatabase
import logging

class ServiceNowService:
    """Service class for ServiceNow integration operations"""
    
    def __init__(self):
        self.servicenow_url = os.environ.get("SERVICENOW_INSTANCE_URL")
        self.servicenow_username = os.environ.get("SERVICENOW_INSTANCE_USERNAME")
        self.servicenow_password = os.environ.get("SERVICENOW_INSTANCE_PASSWORD")
        
        # Neo4j credentials
        self.neo4j_uri = os.environ.get('NEO4J_CONNECTION_URL')
        self.neo4j_username = os.environ.get('NEO4J_USER')
        self.neo4j_password = os.environ.get('NEO4J_PASSWORD')
        
        # Predefined tables
        self.snow_tables = [
            {"label": "Incident", "name": "incident", "primary": "number"},
            {"label": "Change Request", "name": "change_request", "primary": "number"},
            {"label": "Problem", "name": "problem", "primary": "number"},
            {"label": "User", "name": "sys_user", "primary": "name"},
            {"label": "Group", "name": "sys_user_group", "primary": "name"},
            {"label": "Catalog Item", "name": "sc_cat_item", "primary": "name"},
            {"label": "Catalog Task", "name": "sc_task", "primary": "number"},
            {"label": "Knowledge Base", "name": "kb_knowledge", "primary": "number"},
        ]
    
    def flatten_dict(self, d):
        """Flatten nested dictionary structures"""
        flattened = {}
        if hasattr(d, 'items'):
            for k, v in d.items():
                if isinstance(v, dict):
                    flattened[k] = v['display_value']
                elif isinstance(v, list):
                    flattened[k] = json.dumps(v)
                elif v is None:
                    continue
                else:
                    flattened[k] = v
        return flattened
    
    def get_servicenow_data(self, tbl, qp):
        """Fetch data from ServiceNow table"""
        endpoint = f"{self.servicenow_url}/api/now/table/{tbl}"
        params = qp or {}
        params['sysparm_limit'] = params.get('sysparm_limit', 10)
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            response = requests.get(
                endpoint,
                auth=(self.servicenow_username, self.servicenow_password),
                headers=headers,
                params=params
            )
            
            data = response.json()['result']
            return data
            
        except requests.RequestException as e:
            logging.error(f"Error fetching ServiceNow data: {e}")
            return []
    
    def get_tables(self):
        """Get available ServiceNow tables"""
        return self.snow_tables
    
    def get_table_columns(self, table_name):
        """Get columns for a specific table"""
        params = {
            'sysparm_limit': 10,
            'sysparm_query': f"name={table_name}^ORname=task",
            'sysparm_fields': "element,column_label"
        }
        
        data = self.get_servicenow_data("sys_dictionary", params)
        return [self.flatten_dict(record) for record in data]
    
    def get_table_records(self, table_name, page_num=1, page_size=10, 
                         sort_field=None, sort_order=None, filters=None, fields=None):
        """Get records from a specific table"""
        params = {
            'sysparm_limit': page_size,
            'sysparm_offset': (page_num - 1) * page_size,
            'sysparm_display_value': 'all'
        }
        
        if sort_field:
            if sort_order == 'desc':
                params['sysparm_order_by'] = f"{sort_field}^{sort_order}^DESC"
            else:
                params['sysparm_order_by'] = sort_field
        
        if filters:
            params['sysparm_query'] = filters
        
        if fields:
            params['sysparm_fields'] = fields
        
        data = self.get_servicenow_data(table_name, params)
        return [self.flatten_dict(record) for record in data]
    
    def create_neo4j_nodes_relationships(self, data, refs, node_label, unique_key):
        """Create Neo4j nodes and relationships from ServiceNow data"""
        if not all([self.neo4j_uri, self.neo4j_username, self.neo4j_password]):
            raise ValueError("Neo4j credentials not configured")
        
        neo4j_driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_username, self.neo4j_password)
        )
        
        try:
            with neo4j_driver.session() as session:
                primary = next((tab['primary'] for tab in self.snow_tables 
                              if tab['name'] == node_label), 'sys_id')
                
                for row in data:
                    try:
                        flat_row = self.flatten_dict(row)
                        unique_id = flat_row['sys_id']
                        properties = flat_row
                        
                        cypher = f"""
                        MERGE (n:{node_label.upper()} {{`{unique_key}`: $unique_id}})
                        SET n += $properties
                        """
                        
                        for attr, val in row.items():
                            ref = [tup for tup in refs if tup['element'] == attr]
                            if ref and ref[0]['internal_type']['value'] == 'reference':
                                ref_id = val['value']
                                ref_node_label = ref[0]['reference']['value'].upper()
                                relationship_name = attr.upper()
                                ref_node = val['display_value']
                                
                                cypher += f"""
                                MERGE ({attr}:{ref_node_label} {{`name`: '{ref_node}'}})
                                MERGE (n)-[:{relationship_name}]->({attr})
                                """
                        
                        session.run(cypher, {
                            'unique_id': flat_row[unique_key],
                            'properties': properties,
                            'ref_unique_id': ref_id if 'ref_id' in locals() else None,
                            'disp_name': ref_node if 'ref_node' in locals() else None
                        })
                        
                    except Exception as e:
                        logging.error(f"Error creating node for {row.get(unique_key, 'unknown')}: {e}")
        finally:
            neo4j_driver.close()
        
        return {"message": "Export completed successfully"}
    
    def export_to_neo4j(self, table_name, fields=None, filters=None):
        """Export ServiceNow table data to Neo4j"""
        # Get reference columns
        params = {
            'sysparm_limit': 10000,
            'sysparm_query': f"name={table_name}^ORname=task",
            'sysparm_fields': "element,internal_type,reference"
        }
        
        sys_dicts = self.get_servicenow_data("sys_dictionary", params)
        
        # Get table data
        params = {
            'sysparm_limit': 100,
            'sysparm_display_value': 'all'
        }
        
        if filters:
            params['sysparm_query'] = filters
        
        if fields:
            params['sysparm_fields'] = f"sys_id,{fields}"
        
        data = self.get_servicenow_data(table_name, params)
        
        logging.info(f"Fetched {len(data)} records from {table_name}")
        
        return self.create_neo4j_nodes_relationships(
            data, sys_dicts, node_label=table_name, unique_key='sys_id'
        )