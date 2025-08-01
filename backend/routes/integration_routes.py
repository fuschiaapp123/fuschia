from flask import Blueprint, request, jsonify
from integrations import get_integration_manager, IntegrationType
import logging

integration_bp = Blueprint('integrations', __name__)

@integration_bp.route('/integrations/status', methods=['GET'])
def get_integration_status():
    """Get status of all integrations"""
    try:
        integration_manager = get_integration_manager()
        status = integration_manager.test_all_connections()
        available = integration_manager.get_available_integrations()
        
        return jsonify({
            "available_integrations": available,
            "connection_status": status
        })
        
    except Exception as e:
        logging.error(f"Error checking integration status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@integration_bp.route('/integrations/<integration_type>/data', methods=['GET'])
def get_integration_data(integration_type):
    """Get data from specific integration"""
    try:
        table = request.args.get('table', 'incident')
        limit = int(request.args.get('limit', 10))
        
        # Convert string to enum
        integration_enum = None
        for enum_type in IntegrationType:
            if enum_type.value == integration_type:
                integration_enum = enum_type
                break
        
        if not integration_enum:
            return jsonify({"error": f"Unknown integration type: {integration_type}"}), 400
        
        integration_manager = get_integration_manager()
        data = integration_manager.sync_data(integration_enum, table)
        
        return jsonify({
            "integration": integration_type,
            "table": table,
            "count": len(data),
            "data": data[:limit]
        })
        
    except Exception as e:
        logging.error(f"Error fetching integration data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@integration_bp.route('/integrations/<integration_type>/create', methods=['POST'])
def create_integration_record(integration_type):
    """Create record in external system"""
    try:
        data = request.get_json()
        
        if not data or 'table' not in data or 'record_data' not in data:
            return jsonify({"error": "Missing required fields: table, record_data"}), 400
        
        # Convert string to enum
        integration_enum = None
        for enum_type in IntegrationType:
            if enum_type.value == integration_type:
                integration_enum = enum_type
                break
        
        if not integration_enum:
            return jsonify({"error": f"Unknown integration type: {integration_type}"}), 400
        
        integration_manager = get_integration_manager()
        integration = integration_manager.get_integration(integration_enum)
        
        if not integration:
            return jsonify({"error": f"Integration {integration_type} not available"}), 404
        
        result = integration.create_record(data['table'], data['record_data'])
        
        return jsonify({
            "integration": integration_type,
            "table": data['table'],
            "result": result
        })
        
    except Exception as e:
        logging.error(f"Error creating integration record: {str(e)}")
        return jsonify({"error": str(e)}), 500