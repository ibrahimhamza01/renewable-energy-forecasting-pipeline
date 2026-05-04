from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def plot_regional_trends(
    csv_path: str = "website_data/trends/regional_trends.csv",
    output_path: str = "outputs/figures/regional_wind_trends.png",
):
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["region", "date"])

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 6))

    for region, group in df.groupby("region"):
        group = group.sort_values("date")

        # Smooth with rolling average
        group["cf_smooth"] = group["capacity_factor"].rolling(14).mean()

        plt.plot(
            group["date"],
            group["cf_smooth"],
            label=region,
            linewidth=2.5,
        )

    plt.title("Regional Wind Potential Trends (Smoothed, 14-Day Rolling Avg)")
    plt.xlabel("Date")
    plt.ylabel("Capacity Factor")
    plt.legend(title="State", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    linewidth = 3 if region == "TX" else 2
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Wrote figure to {output_path}")


if __name__ == "__main__":
    plot_regional_trends()