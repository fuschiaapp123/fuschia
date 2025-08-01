from flask import Blueprint, request, jsonify
from services.servicenow_service import ServiceNowService
import logging

servicenow_bp = Blueprint('servicenow', __name__)

@servicenow_bp.route('/servicenow/tables', methods=['GET'])
def fetch_servicenow_tables():
    """Get ServiceNow tables"""
    try:
        service = ServiceNowService()
        tables = service.get_tables()
        return jsonify(tables)
    except Exception as e:
        logging.error(f"Error fetching ServiceNow tables: {str(e)}")
        return jsonify({"error": str(e)}), 500

@servicenow_bp.route('/servicenow/columns', methods=['GET'])
def fetch_servicenow_table_columns():
    """Get ServiceNow table columns"""
    try:
        table_name = request.args.get('table')
        if not table_name:
            return jsonify({"error": "Missing table parameter"}), 400
        
        service = ServiceNowService()
        columns = service.get_table_columns(table_name)
        return jsonify(columns)
    except Exception as e:
        logging.error(f"Error fetching ServiceNow columns: {str(e)}")
        return jsonify({"error": str(e)}), 500

@servicenow_bp.route('/servicenow/records', methods=['GET'])
def fetch_servicenow_table_records():
    """Get ServiceNow table records"""
    try:
        table_name = request.args.get('table')
        page_num = request.args.get('page', 1, type=int)
        page_size = request.args.get('size', 10, type=int)
        sort_field = request.args.get('sort_field')
        sort_order = request.args.get('sort_order')
        filters = request.args.get('filters')
        fields = request.args.get('fields')

        if not table_name:
            return jsonify({"error": "Missing table parameter"}), 400

        service = ServiceNowService()
        records = service.get_table_records(
            table_name, page_num, page_size, 
            sort_field, sort_order, filters, fields
        )
        return jsonify(records)
    except Exception as e:
        logging.error(f"Error fetching ServiceNow records: {str(e)}")
        return jsonify({"error": str(e)}), 500

@servicenow_bp.route('/servicenow/export', methods=['GET'])
def export_servicenow_table():
    """Export ServiceNow table data to Neo4j"""
    try:
        table_name = request.args.get('table')
        fields = request.args.get('fields')
        filters = request.args.get('filters')

        if not table_name:
            return jsonify({"error": "Missing table parameter"}), 400

        service = ServiceNowService()
        result = service.export_to_neo4j(table_name, fields, filters)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error exporting ServiceNow data: {str(e)}")
        return jsonify({"error": str(e)}), 500