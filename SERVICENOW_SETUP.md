# ServiceNow Integration Setup

## Overview
The Fuschia platform can integrate with ServiceNow to import data into the knowledge graph. This guide explains how to configure the ServiceNow connection.

## Environment Variables Required

Add these variables to your `.env` file:

```bash
# ServiceNow Configuration
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_INSTANCE_USERNAME=your_username
SERVICENOW_INSTANCE_PASSWORD=your_password
```

## Configuration Steps

### 1. Get Your ServiceNow Instance URL
- Your ServiceNow instance URL typically looks like: `https://company.service-now.com`
- Replace `company` with your actual instance name
- **Important**: Do not include `/api` or any path - just the base URL

### 2. ServiceNow User Credentials
- Use a ServiceNow user account with appropriate permissions
- The user needs read access to:
  - `sys_db_object` (table metadata)
  - `sys_dictionary` (field definitions)
  - Tables you want to import (e.g., `incident`, `change_request`, etc.)

### 3. Required ServiceNow Permissions
The ServiceNow user account needs these roles:
- `rest_api_explorer` (for API access)
- `itil` (for ITSM tables access)
- Additional table-specific roles based on what you want to import

## Testing the Connection

### 1. Using the Backend Test Script
```bash
cd backend
python test_servicenow_connection.py
```

### 2. Using the Frontend
1. Start the backend and frontend servers
2. Login to the application
3. Go to the Data Import tab
4. Check the ServiceNow connection status

## Common Issues and Solutions

### Issue: "ServiceNow credentials not configured"
**Solution**: Ensure all three environment variables are set in your `.env` file

### Issue: "Invalid JSON response from ServiceNow"
**Possible causes:**
- Wrong instance URL (check for typos)
- Incorrect credentials
- ServiceNow instance is down
- User doesn't have required permissions

**Solution**: 
1. Verify your instance URL is correct
2. Test credentials by logging into ServiceNow web interface
3. Check user permissions

### Issue: "Empty response from ServiceNow"
**Possible causes:**
- ServiceNow API endpoints are disabled
- Network connectivity issues
- Authentication problems

**Solution**:
1. Check if you can access the ServiceNow REST API explorer
2. Test with a simple REST API call
3. Verify network connectivity

## Development/Testing Without ServiceNow

If you don't have a ServiceNow instance available, the application will:
1. Use default sample tables for the Data Import interface
2. Show "ServiceNow not configured" status
3. Continue to work with other features

## Security Notes

- Store credentials securely
- Use service accounts with minimal required permissions
- Consider using ServiceNow OAuth for production deployments
- Never commit credentials to version control

## Support

For ServiceNow-specific issues:
1. Check ServiceNow instance logs
2. Verify user permissions in ServiceNow
3. Test API access using ServiceNow REST API Explorer
4. Review ServiceNow documentation for API requirements