# CLAUDE.md

This file provides guidance to Claude Code when working with the MCP Odoo v16 Read-Only server project.

## Project Overview

This is a **Model Context Protocol (MCP) server** implementation for Odoo v16 integration with n8n workflow automation. The server provides **read-only access** to Odoo ERP data using FastMCP framework.

**Repository Structure:**
```
mcp-odoo-v16-read-only/
├── src/                    # MCP server implementation
├── odoo_config.json       # Odoo connection configuration
├── run_server_sync.py     # Main synchronous server
├── run_server_http.py     # HTTP server variant
├── logs/                  # Server logs
├── venv/                  # Python virtual environment
└── CLAUDE.md             # This file
```

## Production Deployment

**Server:** DigitalOcean Droplet "mcp" (159.89.107.191)
**Domain:** mcp.ananda24.de
**Security:** IP-whitelisted Cloud Firewall (n8n: 138.68.72.84, admin: 84.150.214.153)

**Current Configuration:** Read-only user `mcp-read-only@ananda.gmbh`
- **Environment:** Staging (rhholding-merge-add-sscc-23727788)
- **Database:** rhholding-merge-add-sscc-23727788
- **Access Level:** SAMSA Access Management ID 113 (Read-Only)

## Development Commands

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run server locally
python run_server_sync.py

# Check logs
tail -f logs/server.log
```

### Server Deployment
```bash
# SSH to production server
ssh root@159.89.107.191

# Update configuration
scp odoo_config.json root@159.89.107.191:/root/mcp-odoo-v16-read-only/

# Restart server
cd /root/mcp-odoo-v16-read-only
pkill -f run_server
nohup ./venv/bin/python run_server_sync.py > logs/server.log 2>&1 &

# Monitor logs
tail -f logs/server.log
```

## Configuration Management

### Odoo Connection (`odoo_config.json`)
```json
{
  "url": "https://rhholding-merge-add-sscc-23727788.dev.odoo.com",
  "db": "rhholding-merge-add-sscc-23727788",
  "username": "mcp-read-only@ananda.gmbh",
  "password": "mcp88"
}
```

**IMPORTANT:** Always use read-only credentials for production. Never use admin users.

### Security Features
- **IP Whitelisting:** DigitalOcean Cloud Firewall restricts access to n8n server and admin IPs
- **Read-Only User:** SAMSA Access Management enforces read-only operations
- **Domain Filtering:** Access restricted to essential models only

## Available MCP Tools

The server provides these MCP methods for n8n integration:
- `search_employee` - Find employees by name
- `search_holidays` - Query time-off records
- `execute_method` - Generic Odoo model method execution (read-only)

**Example n8n usage:**
```javascript
// Search for employee
const employee = await mcp.search_employee("Andre", 5);

// Get holidays for date range
const holidays = await mcp.search_holidays("2024-01-01", "2024-12-31", employeeId);
```

## Access Management Integration

**SAMSA Access Management ID 113:** "Additional to Role // MCP read only"
- **Read-Only Enforcement:** Prevents all write/create/delete operations
- **Domain Filters:** Restricts access to specific models and records
- **User Assignment:** `mcp-read-only@ananda.gmbh` assigned to this access management

**Domain Filter Examples:**
```python
# Employee access - all employees visible
[('id', '>', 0)]

# Limited company access - specific companies only
[('id', 'in', [1, 2, 3, 4])]
```

## Environment Management

**Never modify n8n configuration** - only the Odoo user credentials change.

**Staging Environment:**
- URL: https://rhholding-merge-add-sscc-23727788.dev.odoo.com
- Database: rhholding-merge-add-sscc-23727788

**Production Environment:**
- URL: https://rhholding.odoo.com
- Database: rhholding-production-10209498

## Troubleshooting

### Common Issues
1. **Port conflicts:** Kill existing processes with `pkill -f run_server`
2. **Authentication errors:** Verify user exists and has correct access management
3. **Connection timeouts:** Check firewall rules and server accessibility

### Debug Commands
```bash
# Check server status
ss -tlnp | grep 8081

# Test authentication
python -c "import xmlrpc.client; print(xmlrpc.client.ServerProxy('https://staging.dev.odoo.com/xmlrpc/2/common').authenticate('db', 'user', 'pass', {}))"

# Monitor real-time logs
tail -f logs/server.log | grep ERROR
```

### Log Analysis
- **INFO:** Normal operations and successful authentications
- **ERROR:** Connection issues, authentication failures, permission errors
- **DEBUG:** Detailed request/response information

## Integration Notes

**n8n Workflow Requirements:**
- MCP server must be accessible from n8n server IP (138.68.72.84)
- Read-only operations only - no data modifications through MCP
- Graceful error handling for access restrictions

**Performance Considerations:**
- Connection pooling enabled for Odoo XML-RPC
- 30-second timeout for all operations
- SSL verification enabled for security

## Architecture Context

This MCP server bridges n8n workflow automation with Odoo ERP, providing secure read-only access to:
- **Employee data** (hr.employee)
- **Time-off records** (hr.leave)
- **Company information** (res.company)
- **Other essential business models**

The read-only restriction ensures data integrity while enabling powerful automation workflows through n8n.