from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def plot_forecast_vs_actual(
    csv_path: str = "website_data/actuals/forecast_vs_actual.csv",
    output_path: str = "outputs/figures/forecast_vs_actual.png",
):
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["actual"], label="Actual", alpha=0.7)
    plt.plot(df["date"], df["predicted"], label="Predicted", linewidth=2)

    region = df["region"].iloc[0] if "region" in df.columns and len(df) > 0 else "Selected Region"

    plt.title(f"Forecast vs Actual Wind Potential — {region}")
    plt.xlabel("Date")
    plt.ylabel("Capacity Factor")
    plt.ylim(0, 0.45)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Wrote figure to {output_path}")


if __name__ == "__main__":
    plot_forecast_vs_actual()