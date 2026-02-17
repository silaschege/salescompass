#!/bin/bash
# ========================================
# SSL Certificate Setup for WebRTC
# SalesCompass CRM
# ========================================

set -e

DOMAIN=${1:-"pbx.salescompass.io"}
EMAIL=${2:-"admin@salescompass.io"}

echo "=========================================="
echo "Setting up SSL certificates for $DOMAIN"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update
    apt-get install -y certbot
fi

echo "Obtaining certificate from Let's Encrypt..."

# Obtain certificate (standalone mode requires port 80 free)
certbot certonly --standalone \
    -d $DOMAIN \
    --non-interactive \
    --agree-tos \
    --email $EMAIL

# Create Asterisk certs directory
echo "Copying certificates to Asterisk..."
mkdir -p /etc/asterisk/certs

cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /etc/asterisk/certs/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /etc/asterisk/certs/

# Set proper ownership and permissions
chown -R asterisk:asterisk /etc/asterisk/certs
chmod 600 /etc/asterisk/certs/privkey.pem
chmod 644 /etc/asterisk/certs/fullchain.pem

# Create renewal hook for automatic updates
echo "Setting up renewal hook..."
cat > /etc/letsencrypt/renewal-hooks/deploy/asterisk.sh << EOF
#!/bin/bash
# Auto-renew hook for Asterisk SSL certificates
DOMAIN=$DOMAIN
cp /etc/letsencrypt/live/\$DOMAIN/fullchain.pem /etc/asterisk/certs/
cp /etc/letsencrypt/live/\$DOMAIN/privkey.pem /etc/asterisk/certs/
chown -R asterisk:asterisk /etc/asterisk/certs
chmod 600 /etc/asterisk/certs/privkey.pem
# Reload Asterisk to pick up new certs
asterisk -rx "core reload" || true
EOF

chmod +x /etc/letsencrypt/renewal-hooks/deploy/asterisk.sh

echo ""
echo "=========================================="
echo "SSL Setup Complete!"
echo "=========================================="
echo "Certificate: /etc/asterisk/certs/fullchain.pem"
echo "Private Key: /etc/asterisk/certs/privkey.pem"
echo ""
echo "Certificates will auto-renew before expiration."
echo "=========================================="
