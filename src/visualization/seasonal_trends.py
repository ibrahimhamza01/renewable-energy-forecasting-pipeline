import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def plot_seasonal_trends():
    df = pd.read_csv("website_data/trends/seasonal_trends.csv")
    df["season"] = df["season"].str.lower()

    Path("outputs/figures").mkdir(parents=True, exist_ok=True)

    regions = df["region"].unique()
    seasons = ["winter", "spring", "summer", "fall"]
    season_labels = ["Winter", "Spring", "Summer", "Fall"]

    plt.figure(figsize=(10, 6))

    for region in regions:
        sub = df[df["region"] == region]
        sub = sub.set_index("season").reindex(seasons)

        plt.plot(
            season_labels,
            sub["capacity_factor"],
            marker="o",
            label=region,
            linewidth=2,
        )

    plt.title("Seasonal Wind Potential by Region (Average Capacity Factor)")
    plt.xlabel("Season")
    plt.ylabel("Average Capacity Factor")
    plt.ylim(0, 0.085)
    plt.legend(title="Region")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    plt.savefig("outputs/figures/seasonal_trends.png", dpi=200)
    plt.close()

    print("Saved seasonal_trends.png")


if __name__ == "__main__":
    plot_seasonal_trends()