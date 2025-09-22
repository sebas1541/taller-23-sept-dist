#!/bin/bash
# Generate basic auth password for Traefik dashboard
# User: admin, Password: secret

echo "Generating basic auth hash for Traefik dashboard..."
echo "Username: admin"
echo "Password: secret"
echo ""
echo "Hash to use in docker-compose.yml:"
echo $(docker run --rm httpd:2.4-alpine htpasswd -nbB admin secret | sed -e 's/\$/\$\$/g')
echo ""
echo "Or if you have htpasswd installed locally:"
echo $(htpasswd -nbB admin secret | sed -e 's/\$/\$\$/g')