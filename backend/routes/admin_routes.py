from flask import Blueprint, jsonify
from datetime import datetime
import logging

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/generate-sample-data', methods=['POST'])
def generate_sample_data():
    """Generate sample data for testing"""
    try:
        from sample_data import SampleDataGenerator
        
        generator = SampleDataGenerator()
        generator.generate_all_sample_data()
        
        return jsonify({
            "message": "Sample data generated successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error generating sample data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/clear-data', methods=['POST'])
def clear_sample_data():
    """Clear all sample data"""
    try:
        from sample_data import SampleDataGenerator
        
        generator = SampleDataGenerator()
        generator.clear_existing_data()
        
        return jsonify({
            "message": "Sample data cleared successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error clearing sample data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        from agents import get_orchestrator
        from integrations import get_integration_manager
        
        # Check database connection
        orchestrator = get_orchestrator()
        db_status = "connected" if orchestrator.neo4j_driver else "disconnected"
        
        # Check integrations
        integration_manager = get_integration_manager()
        integration_status = integration_manager.test_all_connections()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "integrations": integration_status,
            "version": "1.0.0"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500