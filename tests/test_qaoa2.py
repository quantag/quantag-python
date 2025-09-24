import sys
import pandas as pd
from quantag import QAOASolver

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_qaoa2.py <portfolio.csv>")
        sys.exit(1)

    csv_file = sys.argv[1]
    df = pd.read_csv(csv_file)
    assets = list(df["asset"])

    solver = QAOASolver(backend="dwave")

    try:
        result = solver.solve(csv_file, problem="portfolio")
    except Exception as e:
        print("Error while solving:", e)
        sys.exit(1)

    print("Best portfolio solution:")

    # Extract best sample
    if hasattr(result, "first"):
        best_sample = result.first.sample
        energy = result.first.energy
    else:
        # Fallback for pandas DataFrame style output
        best_sample = result.iloc[0, :-2].to_dict()
        energy = result.iloc[0]["energy"]

    # Map binary variables back to asset names
    chosen_assets = [
        assets[i] for i, bit in enumerate(best_sample.values()) if bit == 1
    ]

    print("Selected assets:", chosen_assets)
    print("Energy:", energy)

if __name__ == "__main__":
    main()

