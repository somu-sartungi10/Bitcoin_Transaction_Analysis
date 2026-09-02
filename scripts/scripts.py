import pandas as pd
import numpy as np
import random
import hashlib
from datetime import datetime, timedelta
from faker import Faker
from pathlib import Path


output_path = Path("data/raw/synthetic_raw_data.csv")


fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

NUM_RECORDS = 50000         
ANOMALY_PERCENTAGE = 0.03    # 3% realistic illicit transactions

# Helper to generate realistic Bitcoin addresses
def generate_btc_address(script_type="p2pkh"):
    raw = fake.sha256()[:32]
    if script_type == "p2pkh":
        return f"1{raw[:28]}"
    elif script_type == "p2sh":
        return f"3{raw[:28]}"
    elif script_type == "v0_p2wpkh":
        return f"bc1q{raw[:28].lower()}"
    elif script_type == "v1_p2tr":
        return f"bc1p{raw[:32].lower()}"
    return f"1{raw[:28]}"

# Synthetic ASN & GeoIP pool
GEO_POOLS = [
    {"country": "US", "asn": "AS15169", "isp": "Google LLC", "risk": "low"},
    {"country": "DE", "asn": "AS3320", "isp": "Deutsche Telekom", "risk": "low"},
    {"country": "NL", "asn": "AS60729", "isp": "Tor Exit Relays", "risk": "high"},
    {"country": "RU", "asn": "AS48282", "isp": "Bulletproof Hosting", "risk": "high"},
    {"country": "SC", "asn": "AS9009", "isp": "M247 Offshore", "risk": "high"},
    {"country": "JP", "asn": "AS2516", "isp": "KDDI Corporation", "risk": "low"},
]

# Generate IP pool mapped to ASNs
ip_geo_map = {}
for i in range(1000):
    ip = fake.ipv4_public()
    geo = random.choice(GEO_POOLS)
    ip_geo_map[ip] = geo

# High-risk / Tor IPs pool
tor_bulletproof_ips = [ip for ip, g in ip_geo_map.items() if g["risk"] == "high"]
normal_ips = [ip for ip, g in ip_geo_map.items() if g["risk"] == "low"]

# Wallets and UTXO pool
script_types = ["p2pkh", "p2sh", "v0_p2wpkh", "v1_p2tr"]
wallet_pool = [generate_btc_address(random.choice(script_types)) for _ in range(3000)]

# Active UTXO pool: {address: amount}
utxo_pool = {w: round(random.uniform(0.5, 20.0), 4) for w in wallet_pool[:1000]}

records = []
current_time = datetime(2026, 8, 1, 0, 0, 0)

print(f"🚀 Generating {NUM_RECORDS} Bitcoin Transactions with Multi-Typology Anomaly Injections...")

for i in range(NUM_RECORDS):
    is_anomaly = random.random() < ANOMALY_PERCENTAGE
    txid = f"0x{fake.sha256()}"
    anomaly_type = "normal"
    
    # 2% packet loss / missing network observation
    packet_loss = random.random() < 0.02
    
    if is_anomaly:
        # Choose specific illicit pattern
        pattern = random.choice(["peeling_chain", "coinjoin_mixer", "ransom_fanout", "fast_flux_structuring"])
        anomaly_type = pattern
        
        src_ip = random.choice(tor_bulletproof_ips) if not packet_loss else ""
        src_port = random.choice([9050, 9051, 443, 8333]) if not packet_loss else ""
        dst_ip = random.choice(normal_ips) if not packet_loss else ""
        dst_port = 8333
        
        # Fast burst timing (1 to 10 seconds between illicit steps)
        current_time += timedelta(seconds=random.randint(1, 10))
        
        if pattern == "peeling_chain":
            # 1 input -> 1 small payment + 1 bulk change address
            input_addr = random.choice(list(utxo_pool.keys())[:500])
            peel_change_addr = generate_btc_address("p2pkh")
            merchant_addr = random.choice(wallet_pool)
            
            total_val = round(random.uniform(5.0, 30.0), 4)
            peel_amt = round(random.uniform(0.05, 0.2), 4)
            fee = 0.0005
            change_amt = round(total_val - peel_amt - fee, 4)
            
            input_addresses = [input_addr]
            output_addresses = [merchant_addr, peel_change_addr]
            input_amounts = [total_val]
            output_amounts = [peel_amt, change_amt]
            utxo_pool[peel_change_addr] = change_amt # peel continues
            script_type = "p2pkh"

        elif pattern == "coinjoin_mixer":
            # N equal inputs -> N equal outputs (tumbler signature)
            n_participants = random.randint(4, 8)
            mix_val = 0.5
            fee_per = 0.002
            input_addresses = random.sample(wallet_pool, n_participants)
            output_addresses = [generate_btc_address("v0_p2wpkh") for _ in range(n_participants)]
            input_amounts = [mix_val] * n_participants
            output_amounts = [round(mix_val - fee_per, 4)] * n_participants
            fee = round(fee_per * n_participants, 4)
            script_type = "v0_p2wpkh"

        elif pattern == "ransom_fanout":
            # 1 input -> 15-30 laundry outputs
            num_outputs = random.randint(15, 30)
            total_val = round(random.uniform(15.0, 60.0), 4)
            input_addresses = [random.choice(wallet_pool)]
            output_addresses = [generate_btc_address("p2pkh") for _ in range(num_outputs)]
            input_amounts = [total_val]
            fee = round(total_val * 0.03, 4)
            out_val = round((total_val - fee) / num_outputs, 4)
            output_amounts = [out_val] * num_outputs
            script_type = "p2pkh"

        else: # fast_flux_structuring
            # High frequency bursts under threshold (< 0.5 BTC)
            num_inputs = random.randint(2, 4)
            input_addresses = random.sample(wallet_pool, num_inputs)
            output_addresses = [generate_btc_address("p2sh")]
            total_val = round(random.uniform(0.40, 0.49), 4)
            input_amounts = [round(total_val / num_inputs, 4)] * num_inputs
            fee = 0.0003
            output_amounts = [round(total_val - fee, 4)]
            script_type = "p2sh"

    else:
        # Standard Normal Bitcoin Transactions
        current_time += timedelta(seconds=random.randint(60, 1800))
        src_ip = random.choice(normal_ips) if not packet_loss else ""
        src_port = random.randint(1024, 65535) if not packet_loss else ""
        dst_ip = random.choice(normal_ips) if not packet_loss else ""
        dst_port = 8333
        
        # 1% Coinbase miner reward
        if random.random() < 0.01:
            input_addresses = []
            input_amounts = []
            output_addresses = [random.choice(wallet_pool)]
            output_amounts = [3.125]
            fee = 0.0
            script_type = "v0_p2wpkh"
        else:
            num_inputs = random.randint(1, 2)
            num_outputs = random.randint(1, 2)
            input_addresses = random.sample(wallet_pool, num_inputs)
            output_addresses = random.sample(wallet_pool, num_outputs)
            total_val = round(random.uniform(0.005, 3.5), 4)
            input_amounts = [round(total_val / num_inputs, 4)] * num_inputs
            fee = round(random.uniform(0.0001, 0.001), 5)
            output_amounts = [round((total_val - fee) / num_outputs, 4)] * num_outputs
            script_type = random.choice(script_types)

    # GeoIP / ASN lookup for src_ip
    geo_info = ip_geo_map.get(src_ip, {"country": "", "asn": "", "isp": ""}) if src_ip else {"country": "", "asn": "", "isp": ""}

    records.append({
        "timestamp": int(current_time.timestamp()),
        "src_ip": src_ip,
        "src_port": src_port,
        "dst_ip": dst_ip,
        "dst_port": dst_port,
        "geo_country": geo_info["country"],
        "asn": geo_info["asn"],
        "txid": txid,
        "input_addresses": ";".join(input_addresses),
        "output_addresses": ";".join(output_addresses),
        "input_amounts": ";".join(map(str, input_amounts)),
        "output_amounts": ";".join(map(str, output_amounts)),
        "fee": fee if fee != "" else "",
        "script_type": script_type,
        "is_anomaly": 1 if is_anomaly else 0,
        "pattern_type": anomaly_type
    })

df = pd.DataFrame(records)
print(f"✅ Generated {len(df)} records. Anomaly breakdown:\n{df['pattern_type'].value_counts()}")
df.to_csv(output_path,index=False)
print(f"🗃️ saved to {output_path}")