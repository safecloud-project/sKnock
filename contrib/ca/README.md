# PKI CA for sKnock

The client certificates used in sKnock need to fit inside a single UDP packet.
For this reason, sKnock restricts the client certificates to use ECC keys
derived from the prime256v1 (X9.62/SECG curve over a 256 bit prime field) curve.

This CA is based on a Makefile and requires GNU Make and OpenSSL to be installed.

## Caveats
1. On most \*NIX systems make is aliased to colormake. Since colormake interferes with output printing of interactive commands, the original make should be used instead: `alias make=/usr/bin/make`
2. There is no support for signing CSRs; the certificates are generated after the keys for the entities are locally generated.

## Installation
Copy all the files into a directory and run:

    make init
The command generates the required directories, a CA key and a CA certificate.

## Usage
### To generate a server certificate

    make gen-server-cert NAME=somename
Where `somename` is used as a filename for the key and certificates. The server certificate along with its private key bundled in a PKCS12 bundle whose filepath is displayed after its creation.

## To generate a client certificate

WARNING: It is not an acceptable practise for a service provider to generate client certificates.  The certificates should be generated by the clients and a certificate signing request should be sent to the CA for signing.  The approach documented here is to provide information about how the client certificates are generated, and also to simplify testing or demos.

    make gen-client-cert NAME=somename
This is similar to gen-server-cert.  However, sKnock requires the client certificates to encode an authorization string which specifies what ports at the remote end the client should be able to connect to.  This authorization string is set in `configs/client_config` under the section `altNames` with the key `otherName.1`.

## TODO
Add CRL support


