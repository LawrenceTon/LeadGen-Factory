import dns.resolver
import sys

domain = "google.com"
print(f"Resolving {domain}...")

try:
    answers = dns.resolver.resolve(domain, 'A')
    for rdata in answers:
        print(f"IP: {rdata.address}")
except Exception as e:
    print(f"Error: {e}")
    # Print resolver configuration
    print(f"Resolver nameservers: {dns.resolver.get_default_resolver().nameservers}")
