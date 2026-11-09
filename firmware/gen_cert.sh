#!/bin/sh
# Generate the self-signed HTTPS certificate the Pico uses for the gyro page.
# The private key must stay private: these files are git-ignored. Copy the
# two .der files to the Pico's root:  mpremote cp cert.der :cert.der + cp key.der :key.der
set -e
cat > san.cnf <<'CNF'
[req]
distinguished_name=dn
x509_extensions=v3
prompt=no
[dn]
CN=192.168.4.1
O=Pico Rover
[v3]
subjectAltName=IP:192.168.4.1,DNS:rover.local
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature
extendedKeyUsage=serverAuth
CNF
openssl ecparam -name prime256v1 -genkey -noout -out key.pem
openssl req -new -x509 -key key.pem -days 365 -config san.cnf -out cert.pem
openssl ec -in key.pem -outform DER -out key.der
openssl x509 -in cert.pem -outform DER -out cert.der
rm -f san.cnf
echo "Created cert.der and key.der"
