"""
Lightweight test DNS server using dnslib.

Runs an authoritative DNS server on a configurable port for testing.
Supports A, AAAA, NS, MX, TXT, CNAME, and SOA records.
"""

import socket
import threading
from typing import Any

from dnslib import DNSRecord, DNSHeader, RR, QTYPE, A, AAAA, NS, MX, TXT, CNAME, SOA


class TestDNSServer:
    """A simple authoritative DNS server for testing.

    Usage:
        zones = {
            "example.test.": {
                "A": ["192.0.2.1"],
                "TXT": ["v=spf1 -all"],
            }
        }
        server = TestDNSServer(zones, port=5053)
        server.start()
        # ... run tests ...
        server.stop()
    """

    def __init__(self, zones: dict[str, dict[str, list[Any]]], port: int = 5053, host: str = "127.0.0.1"):
        self.zones = self._normalize_zones(zones)
        self.port = port
        self.host = host
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def _normalize_zones(self, zones: dict) -> dict:
        """Ensure all zone names end with a dot."""
        normalized = {}
        for name, records in zones.items():
            if not name.endswith("."):
                name = name + "."
            normalized[name.lower()] = records
        return normalized

    def start(self):
        """Start the DNS server in a background thread."""
        if self._running:
            return

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        self._socket.settimeout(0.5)  # Allow periodic check for shutdown

        self._running = True
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the DNS server."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._socket:
            self._socket.close()
            self._socket = None

    def _serve(self):
        """Main server loop."""
        while self._running:
            try:
                data, addr = self._socket.recvfrom(512)
                response = self._handle_query(data)
                if response:
                    self._socket.sendto(response, addr)
            except socket.timeout:
                continue
            except Exception:
                continue

    def _handle_query(self, data: bytes) -> bytes | None:
        """Handle a DNS query and return the response."""
        try:
            request = DNSRecord.parse(data)
        except Exception:
            return None

        qname = str(request.q.qname).lower()
        qtype = QTYPE[request.q.qtype]

        reply = DNSRecord(
            DNSHeader(id=request.header.id, qr=1, aa=1, ra=0),
            q=request.q,
        )

        # Look up the zone
        zone = self.zones.get(qname)
        if zone is None:
            # Try parent zones for delegation
            parts = qname.split(".")
            for i in range(1, len(parts)):
                parent = ".".join(parts[i:])
                if parent in self.zones:
                    zone = self.zones[parent]
                    break

        if zone is None:
            # NXDOMAIN
            reply.header.rcode = 3
            return reply.pack()

        # Get records of requested type
        records = zone.get(qtype, [])

        # Handle CNAME chasing
        if not records and "CNAME" in zone:
            for cname_target in zone["CNAME"]:
                reply.add_answer(RR(qname, QTYPE.CNAME, rdata=CNAME(cname_target), ttl=300))
            return reply.pack()

        for record in records:
            rr = self._make_rr(qname, qtype, record)
            if rr:
                reply.add_answer(rr)

        return reply.pack()

    def _make_rr(self, name: str, qtype: str, data: Any) -> RR | None:
        """Create a resource record from zone data."""
        ttl = 300

        if qtype == "A":
            return RR(name, QTYPE.A, rdata=A(data), ttl=ttl)
        elif qtype == "AAAA":
            return RR(name, QTYPE.AAAA, rdata=AAAA(data), ttl=ttl)
        elif qtype == "NS":
            return RR(name, QTYPE.NS, rdata=NS(data), ttl=ttl)
        elif qtype == "MX":
            priority, host = data if isinstance(data, tuple) else (10, data)
            return RR(name, QTYPE.MX, rdata=MX(host, priority), ttl=ttl)
        elif qtype == "TXT":
            return RR(name, QTYPE.TXT, rdata=TXT(data), ttl=ttl)
        elif qtype == "CNAME":
            return RR(name, QTYPE.CNAME, rdata=CNAME(data), ttl=ttl)
        elif qtype == "SOA":
            # data should be (mname, rname, serial, refresh, retry, expire, minimum)
            if isinstance(data, tuple) and len(data) == 7:
                return RR(name, QTYPE.SOA, rdata=SOA(*data), ttl=ttl)
        return None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


if __name__ == "__main__":
    from test_zones import get_all_zones

    zones = get_all_zones()
    print("Starting test DNS server on port 5053...")
    with TestDNSServer(zones, port=5053) as server:
        print("Server running. Test with: dig @127.0.0.1 -p 5053 example.test A")
        print("Press Ctrl+C to stop.")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            print("\nStopping...")
