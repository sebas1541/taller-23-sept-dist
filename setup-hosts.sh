#!/bin/bash

echo "🔧 Setting up /etc/hosts entries for Traefik assignment..."
echo ""

# Check if entries already exist
if grep -q "api.localhost" /etc/hosts && grep -q "ops.localhost" /etc/hosts; then
    echo "/etc/hosts entries already exist!"
    echo ""
    grep "localhost" /etc/hosts
else
    echo "Adding entries to /etc/hosts..."
    echo "You might need to enter your password for sudo access."
    echo ""
    
    # Add entries
    echo "127.0.0.1 api.localhost" | sudo tee -a /etc/hosts
    echo "127.0.0.1 ops.localhost" | sudo tee -a /etc/hosts
    
    echo ""
    echo "Entries added successfully!"
fi

echo ""
echo "Your local domains are ready:"
echo "   • API: http://api.localhost"
echo "   • Traefik Dashboard: http://ops.localhost/dashboard/"
echo "     (username: admin, password: secret)"
echo ""
echo "Now run: docker-compose up --build --scale flask_api=2"