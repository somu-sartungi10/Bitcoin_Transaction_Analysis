import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from faker import Faker
from pathlib import Path


current_file = Path(__file__).resolve()
print(current_file)
root_dir = current_file.parent.parent
print(root_dir)
raw_data_dir = root_dir / "data" / "raw"
output_data  = raw_data_dir / "synthetic_raw_data.csv"

fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

NUM_RECORDS = 100000
ANOMALY_PERCENTAGE = 0.0

print("🚀 Generating Realistic 100000-Row Bitcoin Dataset (With Real-World Missing Data)...")

normal_ips = [fake.ipv4_public() for _ in range(500)]
tor_ips = [f"185.220.{random.randint(101,105)}.{random.randint(1,254)}" for _ in range(25)]
normal_wallets = [f"1{fake.sha256()[:30]}" for _ in range(2000)]
laundry_wallets = [f"1DarkMule{fake.sha256()[:24]}" for _ in range(100)]
script_types = ["p2pkh", "p2sh", "v0_p2wpkh", "v1_p2tr"]

records = []
current_time = datetime(2026, 8, 1, 0, 0, 0)

for i in range(NUM_RECORDS):
    is_anomaly = random.random() < ANOMALY_PERCENTAGE
    
    # --- REALISTIC NETWORK PACKET LOSS (2% Missing IPs) ---
    if random.random() < 0.02:
        src_ip = None
        src_port = None
    elif is_anomaly:
        src_ip = random.choice(tor_ips)
        src_port = random.choice([9050, 9051, 443])
    else:
        src_ip = random.choice(normal_ips)
        src_port = random.randint(1024, 65535)

    dst_ip = random.choice(normal_ips) if random.random() > 0.01 else None
    dst_port = 8333
    txid = f"0x{fake.sha256()}"
    
    if is_anomaly:
        current_time += timedelta(seconds=random.randint(1, 4))
        num_inputs = 1
        num_outputs = random.randint(15, 30)
        input_addresses = random.sample(laundry_wallets, num_inputs)
        output_addresses = random.sample(laundry_wallets, num_outputs)
        
        total_val = round(random.uniform(10.0, 50.0), 4)
        input_amounts = [total_val]
        output_amounts = [round((total_val * 0.95) / num_outputs, 4)] * num_outputs
        fee = round(total_val * 0.05, 4)
        script_type = "p2pkh"
    else:
        current_time += timedelta(seconds=random.randint(300, 3600))
        
        # --- REALISTIC MINER COINBASE TX (1% No Input Addresses) ---
        if random.random() < 0.01:
            input_addresses = []
            input_amounts = []
            num_outputs = 1
            output_addresses = random.sample(normal_wallets, 1)
            total_val = 3.125
            output_amounts = [3.125]
            fee = 0.0
        else:

            
            num_inputs = random.randint(1, 2)
            num_outputs = random.randint(1, 2)
            input_addresses = random.sample(normal_wallets, num_inputs)
            output_addresses = random.sample(normal_wallets, num_outputs)
            total_val = round(random.uniform(0.01, 2.5), 4)
            input_amounts = [round(total_val / num_inputs, 4)] * num_inputs
            output_amounts = [round((total_val * 0.99) / num_outputs, 4)] * num_outputs
            fee = round(total_val * 0.01, 5) if random.random() > 0.01 else None
            
        script_type = random.choice(script_types)

    records.append({
        "timestamp": int(current_time.timestamp()),
        "src_ip": src_ip if src_ip else "",
        "src_port": int(src_port) if src_port else "",
        "dst_ip": dst_ip if dst_ip else "",
        "dst_port": dst_port,
        "txid": txid,
        "input_addresses": ";".join(input_addresses),
        "output_addresses": ";".join(output_addresses),
        "input_amounts": ";".join(map(str, input_amounts)),
        "output_amounts": ";".join(map(str, output_amounts)),
        "fee": fee if fee is not None else "",
        "script_type": script_type
    })

df = pd.DataFrame(records)
df.to_csv(output_data, index=False)
print("✅ Real-World Synthetic Dataset Generated with realistic missing values!")