# Gmail MCP Server Setup Guide

This guide explains how to set up and configure the Gmail MCP (Model Context Protocol) server for the Fuschia Intelligent Automation Platform.

## Overview

The Gmail MCP server enables AI agents to interact with Gmail mailboxes through a standardized protocol. It provides tools for:

- **Reading emails**: List, search, and retrieve email messages
- **Sending emails**: Compose and send new messages
- **Email management**: Modify labels, mark as read/unread
- **Thread management**: Access conversation threads
- **Profile access**: Get Gmail user profile information

## Features

### Available Tools

| Tool Name | Description | Required Parameters |
|-----------|-------------|-------------------|
| `gmail_list_messages` | List Gmail messages with filtering | None (optional: query, max_results, label_ids, page_token) |
| `gmail_get_message` | Get specific message by ID | message_id |
| `gmail_send_message` | Send a new email | to, subject, body |
| `gmail_search_messages` | Search messages with advanced queries | query |
| `gmail_list_labels` | List all Gmail labels | None |
| `gmail_get_profile` | Get user profile information | None |
| `gmail_modify_message` | Modify message labels | message_id |
| `gmail_get_thread` | Get conversation thread | thread_id |

### Available Resources

| Resource | URI | Description |
|----------|-----|-------------|
| Gmail Profile | `gmail://profile` | User profile and account information |
| Gmail Labels | `gmail://labels` | Available Gmail labels and categories |
| Recent Messages | `gmail://messages/recent` | Recent Gmail messages summary |

## Setup Instructions

### Step 1: Google Cloud Console Setup

1. **Create or Select a Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Note the Project ID for reference

2. **Enable Gmail API**
   - In the Cloud Console, navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click on "Gmail API" and press "Enable"

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application" as the application type
   - Give it a name (e.g., "Fuschia Gmail Integration")
   - Click "Create"

4. **Download Credentials**
   - After creating the OAuth client, click the download button
   - Save the file as `credentials.json` in the `/backend/` directory
   - **Important**: Keep this file secure and never commit it to version control

### Step 2: Environment Configuration

1. **Update Environment Variables**

   Add the following to your `/backend/.env` file:

   ```bash
   # Gmail API Configuration
   GMAIL_CREDENTIALS_FILE=credentials.json
   GMAIL_TOKEN_FILE=token.json
   ```

2. **Alternative Credential Paths**

   If you want to store credentials elsewhere, update the paths:

   ```bash
   GMAIL_CREDENTIALS_FILE=/path/to/your/credentials.json
   GMAIL_TOKEN_FILE=/path/to/your/token.json
   ```

### Step 3: Initial Authentication

1. **Install Dependencies**

   The required dependencies should already be installed. If not:

   ```bash
   cd backend
   source venv/bin/activate
   pip install google-auth google-auth-oauthlib google-api-python-client
   ```

2. **Test the Setup**

   Run the test script to verify everything is working:

   ```bash
   cd backend
   source venv/bin/activate
   python test_gmail_mcp.py
   ```

3. **First-Time Authentication**

   When you first use the Gmail MCP server with real credentials:
   - A browser window will open asking for Google account authorization
   - Sign in with the Gmail account you want to access
   - Grant the necessary permissions
   - The server will save a `token.json` file for future use

### Step 4: Integration with Fuschia Platform

1. **Register the MCP Server**

   The Gmail MCP server is automatically registered. You can verify by calling:

   ```bash
   POST /api/v1/mcp/servers/predefined
   ```

2. **Verify Server Status**

   Check the server status:

   ```bash
   GET /api/v1/mcp/status
   ```

3. **List Available Tools**

   Get the available Gmail tools:

   ```bash
   GET /api/v1/mcp/servers/gmail-api/tools
   ```

## Usage Examples

### Execute Gmail Tools via API

1. **List Recent Messages**

   ```bash
   POST /api/v1/mcp/tools/execute
   {
     "tool_name": "gmail_list_messages",
     "arguments": {
       "max_results": 10,
       "query": "is:unread"
     }
   }
   ```

2. **Send an Email**

   ```bash
   POST /api/v1/mcp/tools/execute
   {
     "tool_name": "gmail_send_message",
     "arguments": {
       "to": "recipient@example.com",
       "subject": "Hello from Fuschia",
       "body": "This is a test email sent via the Gmail MCP server."
     }
   }
   ```

3. **Search Messages**

   ```bash
   POST /api/v1/mcp/tools/execute
   {
     "tool_name": "gmail_search_messages",
     "arguments": {
       "query": "from:important@company.com",
       "max_results": 5
   }
   ```

### Gmail Search Query Examples

The Gmail search functionality supports Google's search operators:

- `from:email@domain.com` - Messages from specific sender
- `to:email@domain.com` - Messages to specific recipient
- `subject:keyword` - Messages with keyword in subject
- `is:unread` - Unread messages
- `is:read` - Read messages
- `has:attachment` - Messages with attachments
- `label:important` - Messages with specific label
- `after:2023/01/01` - Messages after date
- `before:2023/12/31` - Messages before date

## Security Considerations

### OAuth 2.0 Scopes

The Gmail MCP server requests the following scopes:

- `https://www.googleapis.com/auth/gmail.readonly` - Read access to Gmail
- `https://www.googleapis.com/auth/gmail.send` - Send emails
- `https://www.googleapis.com/auth/gmail.compose` - Compose emails
- `https://www.googleapis.com/auth/gmail.modify` - Modify labels and read status

### Security Best Practices

1. **Credential Protection**
   - Never commit `credentials.json` or `token.json` to version control
   - Store credentials securely in production environments
   - Use environment variables or secure vaults for credential paths

2. **Access Control**
   - Limit which users can execute Gmail tools
   - Implement proper authentication and authorization
   - Log all Gmail API operations for audit purposes

3. **Rate Limiting**
   - Gmail API has quotas and rate limits
   - Implement appropriate retry logic and backoff strategies
   - Monitor API usage to avoid quota exhaustion

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify `credentials.json` is in the correct location
   - Check that Gmail API is enabled in Google Cloud Console
   - Ensure OAuth consent screen is configured

2. **Permission Errors**
   - Verify the OAuth client has the correct scopes
   - Re-authorize if scopes have changed
   - Check that the user has granted all required permissions

3. **Token Refresh Issues**
   - Delete `token.json` and re-authenticate
   - Verify the refresh token hasn't expired
   - Check OAuth client configuration

### Testing Without Authentication

You can test the server structure without authentication:

```bash
cd backend
python test_gmail_mcp.py
```

This will show all available tools and their schemas, even without valid credentials.

### Logs and Debugging

Enable debug logging by setting the log level:

```python
import logging
logging.getLogger('app.services.gmail_mcp_server').setLevel(logging.DEBUG)
```

## API Reference

### Server Information

- **Server ID**: `gmail-api`
- **Name**: Gmail API Server
- **Version**: 1.0.0
- **Capabilities**: Tools, Resources (no Prompts)

### Error Handling

The Gmail MCP server handles errors gracefully:

- Authentication errors return clear messages
- API rate limit errors include retry information
- Invalid parameters return validation messages
- Network errors are properly caught and reported

### Integration Status

The Gmail MCP server is fully integrated with:

- ✅ MCP Server Manager
- ✅ MCP Tool Bridge
- ✅ REST API Endpoints
- ✅ Database Persistence
- ✅ Agent Tool Execution

## Support and Development

For issues or feature requests related to the Gmail MCP server:

1. Check the logs for error messages
2. Verify Google Cloud Console configuration
3. Test with the provided test script
4. Review the Gmail API documentation for advanced features

The Gmail MCP server is designed to be extensible and can be enhanced with additional Gmail API features as needed.