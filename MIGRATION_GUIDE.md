# Migration Guide: Dynamic Configuration

This document describes the migration from hardcoded hosts and ports to dynamic environment-based configuration.

## Summary of Changes

### 🔒 Critical Security Fix
- **REMOVED**: Hardcoded Evolution API key from `.mcp.json`
- **REMOVED**: Hardcoded private IP address `192.168.112.142`
- **REQUIRED**: Environment variables must now be set for WhatsApp integration

### 🌐 Dynamic Host/Port Configuration  
- **API Base URLs**: Automatically detect host configuration (localhost vs. configured host)
- **Python Code**: All hardcoded hosts/ports converted to use environment variables
- **MCP Configuration**: Kept as local file (git ignored) for simplicity

## Migration Steps

### 1. Setup MCP Configuration  
```bash
# Copy MCP template to local configuration
cp .mcp.json.example .mcp.json

# Edit .mcp.json with your specific values:
# - Evolution API host, credentials, instance name
# - Any custom ports/hosts for local services
```

### 2. Update External References
If you have external scripts or documentation that reference:
- `http://localhost:9888` - Update to use `HIVE_API_HOST:HIVE_API_PORT`
- `192.168.112.142:8080` - Update to use `EVOLUTION_API_HOST:EVOLUTION_API_PORT`
- Hardcoded database URLs - Update to use environment variables

## File Changes

### Configuration Files
- ✅ `.gitignore` - Added `.mcp.json` to prevent committing local config
- ✅ `.mcp.json.example` - Template for local MCP configuration

### Code Files
- ✅ `lib/config/server_config.py` - Enhanced `get_base_url()` for dynamic host detection
- ✅ `common/startup_notifications.py` - Use dynamic server configuration
- ✅ `api/serve.py` - Use dynamic base URL for development information
- ✅ `common/startup_display.py` - Use dynamic API URL display

## Backward Compatibility

### ⚠️ Breaking Changes
1. **MCP Configuration**: Must copy `.mcp.json.example` to `.mcp.json` and configure
2. **WhatsApp Integration**: Must update credentials in local `.mcp.json`
3. **Private Network Access**: Update any references to `192.168.112.142`

### ✅ Compatible Changes
1. **API Host Detection**: Automatically handles `0.0.0.0` vs. specific hosts
2. **Development Workflow**: Standard localhost development unchanged
3. **Database Configuration**: Existing environment variables still work

### Security Verification
```bash
# Verify no secrets in version control
grep -r "BEE0266C" . --exclude-dir=.git
# Should return no results

# Verify no hardcoded IPs
grep -r "192.168.112.142" . --exclude-dir=.git --exclude="MIGRATION_GUIDE.md"
# Should return no results
```

## Production Deployment

### Environment Variables Checklist
- [ ] `EVOLUTION_API_HOST` - Set to your Evolution API server
- [ ] `EVOLUTION_API_API_KEY` - Set to secure API key (not the old exposed one)
- [ ] `EVOLUTION_API_INSTANCE` - Set to your instance name
- [ ] `HIVE_API_HOST` - Set to `0.0.0.0` for production binding
- [ ] `HIVE_API_PORT` - Set to your desired port (default: 8886)
- [ ] `HIVE_DATABASE_URL` - Set to your production database URL

### Security Best Practices
1. **Rotate API Keys**: Generate new Evolution API key (old one was exposed)
2. **Network Security**: Configure firewall rules for new dynamic hosts
3. **Access Control**: Restrict MCP server access to authorized hosts only
4. **Monitoring**: Monitor for unauthorized access attempts using old hardcoded values

## Troubleshooting

### Common Issues
1. **MCP Connection Failed**: Check that environment variables are set correctly
2. **WhatsApp Not Working**: Verify Evolution API credentials and host accessibility
3. **Database Connection Error**: Check database host, port, and credentials
4. **API URLs Wrong**: Verify `HIVE_API_HOST` and `HIVE_API_PORT` settings

### Debug Commands
```bash
# Check environment variables
env | grep -E "(MCP_|EVOLUTION_|HIVE_)"

# Test MCP configuration processing
python scripts/configure_mcp.py

# Validate server configuration
python -c "from lib.config.server_config import get_server_config; print(get_server_config())"
```

## Support

If you encounter issues with the migration:
1. Check this migration guide for common solutions
2. Verify all environment variables are set correctly
3. Test with the validation scripts provided
4. Review logs for specific error messages related to configuration