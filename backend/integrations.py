"""
External system integrations for Fuschia platform
Provides connectors for ServiceNow, Salesforce, SAP, and Workday
"""

import requests
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    """Types of external integrations"""
    SERVICENOW = "servicenow"
    SALESFORCE = "salesforce"
    SAP = "sap"
    WORKDAY = "workday"

@dataclass
class IntegrationConfig:
    """Configuration for external system integration"""
    integration_type: IntegrationType
    base_url: str
    username: str
    password: str
    api_key: Optional[str] = None
    additional_headers: Optional[Dict[str, str]] = None

class BaseIntegration(ABC):
    """Abstract base class for all integrations"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.session = requests.Session()
        self._setup_authentication()
    
    @abstractmethod
    def _setup_authentication(self):
        """Setup authentication for the integration"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the integration is working"""
        pass
    
    @abstractmethod
    def get_records(self, table: str, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get records from the external system"""
        pass
    
    @abstractmethod
    def create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the external system"""
        pass
    
    @abstractmethod
    def update_record(self, table: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record"""
        pass

class ServiceNowIntegration(BaseIntegration):
    """ServiceNow integration implementation"""
    
    def _setup_authentication(self):
        """Setup basic authentication for ServiceNow"""
        self.session.auth = (self.config.username, self.config.password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        if self.config.additional_headers:
            self.session.headers.update(self.config.additional_headers)
    
    def test_connection(self) -> bool:
        """Test ServiceNow connection"""
        try:
            response = self.session.get(f"{self.config.base_url}/api/now/table/sys_user?sysparm_limit=1")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ServiceNow connection test failed: {e}")
            return False
    
    def get_records(self, table: str, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get records from ServiceNow table"""
        try:
            url = f"{self.config.base_url}/api/now/table/{table}"
            params = {
                'sysparm_limit': limit,
                'sysparm_display_value': 'all'
            }
            
            if filters:
                query_parts = []
                for key, value in filters.items():
                    query_parts.append(f"{key}={value}")
                params['sysparm_query'] = '^'.join(query_parts)
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json().get('result', [])
            
        except Exception as e:
            logger.error(f"Failed to get ServiceNow records: {e}")
            return []
    
    def create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create record in ServiceNow"""
        try:
            url = f"{self.config.base_url}/api/now/table/{table}"
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            return response.json().get('result', {})
            
        except Exception as e:
            logger.error(f"Failed to create ServiceNow record: {e}")
            return {}
    
    def update_record(self, table: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update ServiceNow record"""
        try:
            url = f"{self.config.base_url}/api/now/table/{table}/{record_id}"
            response = self.session.put(url, json=data)
            response.raise_for_status()
            
            return response.json().get('result', {})
            
        except Exception as e:
            logger.error(f"Failed to update ServiceNow record: {e}")
            return {}

class SalesforceIntegration(BaseIntegration):
    """Salesforce integration implementation"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.access_token = None
        self.instance_url = None
    
    def _setup_authentication(self):
        """Setup OAuth authentication for Salesforce"""
        try:
            # OAuth 2.0 authentication
            auth_url = f"{self.config.base_url}/services/oauth2/token"
            auth_data = {
                'grant_type': 'password',
                'client_id': self.config.api_key,
                'client_secret': self.config.password,
                'username': self.config.username,
                'password': self.config.password
            }
            
            response = requests.post(auth_url, data=auth_data)
            if response.status_code == 200:
                auth_result = response.json()
                self.access_token = auth_result['access_token']
                self.instance_url = auth_result['instance_url']
                
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                })
            else:
                logger.error(f"Salesforce authentication failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Salesforce authentication error: {e}")
    
    def test_connection(self) -> bool:
        """Test Salesforce connection"""
        if not self.access_token:
            return False
        
        try:
            response = self.session.get(f"{self.instance_url}/services/data/v57.0/sobjects/")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Salesforce connection test failed: {e}")
            return False
    
    def get_records(self, table: str, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get records from Salesforce"""
        try:
            base_query = f"SELECT Id, Name FROM {table}"
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = '{value}'")
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += f" LIMIT {limit}"
            
            url = f"{self.instance_url}/services/data/v57.0/query/"
            params = {'q': base_query}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json().get('records', [])
            
        except Exception as e:
            logger.error(f"Failed to get Salesforce records: {e}")
            return []
    
    def create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create record in Salesforce"""
        try:
            url = f"{self.instance_url}/services/data/v57.0/sobjects/{table}/"
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to create Salesforce record: {e}")
            return {}
    
    def update_record(self, table: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update Salesforce record"""
        try:
            url = f"{self.instance_url}/services/data/v57.0/sobjects/{table}/{record_id}"
            response = self.session.patch(url, json=data)
            response.raise_for_status()
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Failed to update Salesforce record: {e}")
            return {}

class SAPIntegration(BaseIntegration):
    """SAP integration implementation (simplified)"""
    
    def _setup_authentication(self):
        """Setup authentication for SAP"""
        self.session.auth = (self.config.username, self.config.password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-CSRF-Token': 'Fetch'
        })
    
    def test_connection(self) -> bool:
        """Test SAP connection"""
        try:
            # Mock SAP connection test
            response = self.session.get(f"{self.config.base_url}/sap/opu/odata/sap/API_BUSINESS_PARTNER/")
            return response.status_code in [200, 401]  # 401 is expected without proper auth
        except Exception as e:
            logger.error(f"SAP connection test failed: {e}")
            return False
    
    def get_records(self, table: str, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get records from SAP (mock implementation)"""
        # Mock SAP data
        return [
            {
                "BusinessPartner": "1000001",
                "BusinessPartnerName": "Sample Customer 1",
                "BusinessPartnerCategory": "2"
            },
            {
                "BusinessPartner": "1000002", 
                "BusinessPartnerName": "Sample Customer 2",
                "BusinessPartnerCategory": "2"
            }
        ]
    
    def create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create record in SAP (mock implementation)"""
        # Mock creation
        return {"BusinessPartner": "1000003", "status": "created"}
    
    def update_record(self, table: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update SAP record (mock implementation)"""
        # Mock update
        return {"BusinessPartner": record_id, "status": "updated"}

class WorkdayIntegration(BaseIntegration):
    """Workday integration implementation (simplified)"""
    
    def _setup_authentication(self):
        """Setup authentication for Workday"""
        self.session.auth = (self.config.username, self.config.password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def test_connection(self) -> bool:
        """Test Workday connection"""
        try:
            # Mock Workday connection test
            return True  # Mock success
        except Exception as e:
            logger.error(f"Workday connection test failed: {e}")
            return False
    
    def get_records(self, table: str, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get records from Workday (mock implementation)"""
        # Mock Workday employee data
        return [
            {
                "Employee_ID": "E001",
                "Name": "John Doe",
                "Position": "Software Engineer",
                "Department": "Engineering"
            },
            {
                "Employee_ID": "E002",
                "Name": "Jane Smith", 
                "Position": "Product Manager",
                "Department": "Product"
            }
        ]
    
    def create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create record in Workday (mock implementation)"""
        # Mock creation
        return {"Employee_ID": "E003", "status": "created"}
    
    def update_record(self, table: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update Workday record (mock implementation)"""
        # Mock update
        return {"Employee_ID": record_id, "status": "updated"}

class IntegrationManager:
    """Manages all external system integrations"""
    
    def __init__(self):
        self.integrations: Dict[IntegrationType, BaseIntegration] = {}
        self._load_integrations()
    
    def _load_integrations(self):
        """Load integration configurations from environment"""
        # ServiceNow
        servicenow_url = os.environ.get('SERVICENOW_INSTANCE_URL')
        servicenow_user = os.environ.get('SERVICENOW_INSTANCE_USERNAME')
        servicenow_pass = os.environ.get('SERVICENOW_INSTANCE_PASSWORD')
        
        if all([servicenow_url, servicenow_user, servicenow_pass]):
            config = IntegrationConfig(
                integration_type=IntegrationType.SERVICENOW,
                base_url=servicenow_url,
                username=servicenow_user,
                password=servicenow_pass
            )
            self.integrations[IntegrationType.SERVICENOW] = ServiceNowIntegration(config)
            logger.info("ServiceNow integration configured")
        
        # Salesforce (example configuration)
        salesforce_url = os.environ.get('SALESFORCE_INSTANCE_URL', 'https://login.salesforce.com')
        salesforce_user = os.environ.get('SALESFORCE_USERNAME')
        salesforce_pass = os.environ.get('SALESFORCE_PASSWORD')
        salesforce_key = os.environ.get('SALESFORCE_CLIENT_ID')
        
        if all([salesforce_user, salesforce_pass, salesforce_key]):
            config = IntegrationConfig(
                integration_type=IntegrationType.SALESFORCE,
                base_url=salesforce_url,
                username=salesforce_user,
                password=salesforce_pass,
                api_key=salesforce_key
            )
            self.integrations[IntegrationType.SALESFORCE] = SalesforceIntegration(config)
            logger.info("Salesforce integration configured")
        
        # SAP (mock configuration)
        sap_url = os.environ.get('SAP_BASE_URL', 'https://mock-sap-system.com')
        sap_user = os.environ.get('SAP_USERNAME', 'mock_user')
        sap_pass = os.environ.get('SAP_PASSWORD', 'mock_pass')
        
        config = IntegrationConfig(
            integration_type=IntegrationType.SAP,
            base_url=sap_url,
            username=sap_user,
            password=sap_pass
        )
        self.integrations[IntegrationType.SAP] = SAPIntegration(config)
        logger.info("SAP integration configured (mock)")
        
        # Workday (mock configuration)
        workday_url = os.environ.get('WORKDAY_BASE_URL', 'https://mock-workday-system.com')
        workday_user = os.environ.get('WORKDAY_USERNAME', 'mock_user')
        workday_pass = os.environ.get('WORKDAY_PASSWORD', 'mock_pass')
        
        config = IntegrationConfig(
            integration_type=IntegrationType.WORKDAY,
            base_url=workday_url,
            username=workday_user,
            password=workday_pass
        )
        self.integrations[IntegrationType.WORKDAY] = WorkdayIntegration(config)
        logger.info("Workday integration configured (mock)")
    
    def get_integration(self, integration_type: IntegrationType) -> Optional[BaseIntegration]:
        """Get a specific integration"""
        return self.integrations.get(integration_type)
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Test all integration connections"""
        results = {}
        for integration_type, integration in self.integrations.items():
            results[integration_type.value] = integration.test_connection()
        return results
    
    def get_available_integrations(self) -> List[str]:
        """Get list of available integrations"""
        return [integration_type.value for integration_type in self.integrations.keys()]
    
    def sync_data(self, integration_type: IntegrationType, table: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Sync data from external system"""
        integration = self.get_integration(integration_type)
        if not integration:
            logger.error(f"Integration {integration_type.value} not found")
            return []
        
        try:
            return integration.get_records(table, filters)
        except Exception as e:
            logger.error(f"Failed to sync data from {integration_type.value}: {e}")
            return []

# Global integration manager instance
integration_manager = IntegrationManager()

def get_integration_manager() -> IntegrationManager:
    """Get the global integration manager instance"""
    return integration_manager