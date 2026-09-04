from pathlib import Path
import ipaddress
import math
from typing import Dict, Any, Optional
import geoip2.database
import geoip2.errors

class GeoIPDatabaseManager:
    """
    Official offline MaxMind .mmdb reader for Bitcoin forensic IP enrichment.
    Queries GeoLite2-City.mmdb and GeoLite2-ASN.mmdb directly at microsecond speeds.
    """

    # High-Risk / Bulletproof Hosting / VPN / Tor ASNs for forensic tagging
    KNOWN_ANONYMIZER_ASNS = {
        "AS60729": "Tor Exit Relay Network",
        "AS48282": "Bulletproof Hosting (RU)",
        "AS9009":  "M247 Offshore Proxy",
        "AS200052": "FlokiNET Anonymous Host",
        "AS39351": "LeaseWeb Tor Relays",
        "AS202425": "IP-Volume Bulletproof"
    }

    # Major Datacenter / Cloud ASNs (Automated botnet servers)
    KNOWN_DATACENTER_ASNS = {
        "AS16509", "AS14618", "AS16276", "AS24940", "AS14061",  # AWS, OVH, DigitalOcean, Hetzner
        "AS8075", "AS15169", "AS13335"                          # Microsoft, Google Cloud, Cloudflare
    }

    def __init__(self, geoip_dir: Optional[Path] = None):
        """
        Initializes the official MaxMind .mmdb database readers.
        """
        if geoip_dir is None:
            self.geoip_dir = Path(__file__).resolve().parent.parent / "data" / "geoip"
        else:
            self.geoip_dir = Path(geoip_dir)

        self.city_db_path = self.geoip_dir / "GeoLite2-City.mmdb"
        self.asn_db_path = self.geoip_dir / "GeoLite2-ASN.mmdb"

        # Verify files exist
        if not self.city_db_path.exists():
            print(f"⚠️ Warning: City DB not found at {self.city_db_path}")
        if not self.asn_db_path.exists():
            print(f"⚠️ Warning: ASN DB not found at {self.asn_db_path}")

        # Initialize official GeoIP2 Readers
        self.city_reader = geoip2.database.Reader(str(self.city_db_path)) if self.city_db_path.exists() else None
        self.asn_reader = geoip2.database.Reader(str(self.asn_db_path)) if self.asn_db_path.exists() else None

    def lookup_ip(self, ip_str: str) -> Dict[str, Any]:
        """
        Queries the .mmdb files for a given IP address.
        Returns: country, continent, coordinates (lat/lon), timezone, ASN, organization, and risk flags.
        """
        clean_ip = str(ip_str).strip()
        
        # Default response for missing or invalid IPs
        default_record = {
            "ip": clean_ip,
            "geo_country": "UNKNOWN",
            "continent": "UNKNOWN",
            "city": "Unknown",
            "latitude": 0.0,
            "longitude": 0.0,
            "timezone": "UTC",
            "asn": "UNKNOWN_ASN",
            "isp_org": "Unknown",
            "is_datacenter": 0.0,
            "is_anonymizer": 0.0
        }

        if not clean_ip or clean_ip in ["0.0.0.0", "None", "nan", ""]:
            return default_record

        # Check for Private LAN IPs (192.168.x, 10.x, 127.0.0.1)
        try:
            ip_obj = ipaddress.ip_address(clean_ip)
            if ip_obj.is_private or ip_obj.is_loopback:
                default_record.update({
                    "geo_country": "LOCAL",
                    "continent": "LOCAL",
                    "city": "Private Network",
                    "asn": "PRIVATE_NET",
                    "isp_org": "LAN / Localhost"
                })
                return default_record
        except ValueError:
            return default_record

        res = default_record.copy()

        # 1. Query GeoLite2-City.mmdb
        if self.city_reader:
            try:
                city_resp = self.city_reader.city(clean_ip)
                res["geo_country"] = city_resp.country.iso_code or "UNKNOWN"
                res["continent"] = city_resp.continent.code or "UNKNOWN"
                res["city"] = city_resp.city.name or "Unknown"
                res["latitude"] = float(city_resp.location.latitude or 0.0)
                res["longitude"] = float(city_resp.location.longitude or 0.0)
                res["timezone"] = city_resp.location.time_zone or "UTC"
            except (geoip2.errors.AddressNotFoundError, ValueError):
                pass  # IP not in database

        # 2. Query GeoLite2-ASN.mmdb
        if self.asn_reader:
            try:
                asn_resp = self.asn_reader.asn(clean_ip)
                if asn_resp.autonomous_system_number:
                    res["asn"] = f"AS{asn_resp.autonomous_system_number}"
                res["isp_org"] = asn_resp.autonomous_system_organization or "Unknown"
            except (geoip2.errors.AddressNotFoundError, ValueError):
                pass

        # 3. Derive Forensic Infrastructure Flags
        asn_str = res["asn"]
        org_str = res["isp_org"]

        if asn_str in self.KNOWN_DATACENTER_ASNS or any(w in org_str for w in ["Cloud", "Hosting", "Server", "Hetzner", "DigitalOcean"]):
            res["is_datacenter"] = 1.0

        if asn_str in self.KNOWN_ANONYMIZER_ASNS or any(w in org_str for w in ["Tor", "VPN", "Proxy", "Exit"]):
            res["is_anonymizer"] = 1.0

        return res

    def close(self):
        """Closes the .mmdb file handles properly."""
        if self.city_reader:
            self.city_reader.close()
        if self.asn_reader:
            self.asn_reader.close()

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Computes distance between two coordinates in kilometers."""
        if (lat1 == 0.0 and lon1 == 0.0) or (lat2 == 0.0 and lon2 == 0.0):
            return 0.0
        r = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
        return float(r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)))