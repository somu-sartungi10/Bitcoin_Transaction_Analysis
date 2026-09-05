import csv
import io
import pandas as pd


def load_raw_csv(path):
    """
    Ye function hamari CSV file ko sahi tarike se padhta hai.
    
    Simple samajh: file mein har line do baar quotes mein wrapped hai
    (jaisa ek gift do baar pack kiya gaya ho), isliye hum use 2 baar
    "unwrap" karte hain taaki asli data mil sake.
    """
    with open(path, encoding="utf-8", newline="") as f:
        outer_rows = list(csv.reader(f))

    # Pehla unwrap - header (column names) nikalo
    header = next(csv.reader(io.StringIO(outer_rows[0][0])))

    # Doosra unwrap - baaki saari data rows nikalo
    rows = [next(csv.reader(io.StringIO(r[0]))) for r in outer_rows[1:]]

    df = pd.DataFrame(rows, columns=header)
    return df


if __name__ == "__main__":
    df = load_raw_csv("data/raw/cleaned_transactions_final.csv")
    print("Shape (rows, columns):", df.shape)
    print()
    print("Column names:")
    print(list(df.columns))
    print()
    print("Pehli 3 rows:")
    print(df.head(3))