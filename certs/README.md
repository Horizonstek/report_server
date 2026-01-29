# SSL Certificates

Place your SSL certificates in this directory:

- `cert.pem` - SSL certificate file
- `key.pem` - SSL private key file

## Generate Self-Signed Certificates (for development/testing)

### Using OpenSSL:
```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=localhost"
```

### Using PowerShell (Windows):
```powershell
# Generate self-signed certificate
$cert = New-SelfSignedCertificate -DnsName "localhost" -CertStoreLocation "Cert:\CurrentUser\My" -NotAfter (Get-Date).AddYears(1)

# Export certificate and key
$pwd = ConvertTo-SecureString -String "password" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath .\cert.pfx -Password $pwd

# Convert PFX to PEM (requires OpenSSL)
openssl pkcs12 -in cert.pfx -out cert.pem -nokeys
openssl pkcs12 -in cert.pfx -out key.pem -nodes -nocerts
```

## Security Note
- Never commit real certificates to version control
- Use proper certificates from a CA in production
- Keep private keys secure with appropriate permissions
