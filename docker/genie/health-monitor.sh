#!/bin/bash
# Health check script combines PostgreSQL and API checks

while true; do
    # Check PostgreSQL health
    if pg_isready -h localhost -p 5432 -U hive -d hive_genie > /dev/null 2>&1; then
        pg_status="healthy"
    else
        pg_status="unhealthy"
    fi
    
    # Check API health  
    if curl -f http://localhost:45886/api/v1/health > /dev/null 2>&1; then
        api_status="healthy"
    else
        api_status="unhealthy"
    fi
    
    echo "$(date): PostgreSQL: $pg_status, API: $api_status"
    
    # Sleep for 30 seconds
    sleep 30
done