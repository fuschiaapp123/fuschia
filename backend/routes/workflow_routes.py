from flask import Blueprint, request, jsonify
import os
import logging

workflow_bp = Blueprint('workflows', __name__)

@workflow_bp.route('/workflows/create', methods=['POST'])
def create_workflow():
    """Create a new workflow from YAML definition"""
    try:
        data = request.get_json()
        
        if not data or 'workflow' not in data:
            return jsonify({"error": "Missing workflow definition"}), 400
        
        workflow_data = data['workflow']
        workflow_id = data.get('id', f"workflow_{len(os.listdir('data'))}")
        
        # Save workflow to file
        workflow_path = f"data/process-map-{workflow_id}.yaml"
        with open(workflow_path, 'w') as f:
            f.write(workflow_data)
        
        return jsonify({
            "message": "Workflow created successfully",
            "workflow_id": workflow_id,
            "path": workflow_path
        })
        
    except Exception as e:
        logging.error(f"Error creating workflow: {str(e)}")
        return jsonify({"error": str(e)}), 500

@workflow_bp.route('/workflows/list', methods=['GET'])
def list_workflows():
    """List all available workflows"""
    try:
        workflows = []
        data_dir = "data"
        
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.startswith('process-map-') and file.endswith('.yaml'):
                    workflow_id = file.replace('process-map-', '').replace('.yaml', '')
                    workflows.append({
                        "id": workflow_id,
                        "filename": file,
                        "path": os.path.join(data_dir, file)
                    })
        
        return jsonify({"workflows": workflows})
        
    except Exception as e:
        logging.error(f"Error listing workflows: {str(e)}")
        return jsonify({"error": str(e)}), 500

@workflow_bp.route('/workflows/<workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """Get specific workflow definition"""
    try:
        workflow_path = f"data/process-map-{workflow_id}.yaml"
        
        if not os.path.exists(workflow_path):
            return jsonify({"error": f"Workflow {workflow_id} not found"}), 404
        
        with open(workflow_path, 'r') as f:
            workflow_content = f.read()
        
        return jsonify({
            "workflow_id": workflow_id,
            "content": workflow_content
        })
        
    except Exception as e:
        logging.error(f"Error fetching workflow: {str(e)}")
        return jsonify({"error": str(e)}), 500