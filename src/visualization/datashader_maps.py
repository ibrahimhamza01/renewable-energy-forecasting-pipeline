from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def plot_us_wind_station_map(
    csv_path: str = "website_data/maps/us_wind_station_map.csv",
    output_path: str = "outputs/figures/us_wind_potential_map.png",
):
    df = pd.read_csv(csv_path)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 7))

    scatter = plt.scatter(
        df["longitude"],
        df["latitude"],
        c=df["avg_wind_speed_ms"],
        s=20,
        alpha=0.8,
    )

    plt.colorbar(scatter, label="Average Wind Speed (m/s)")
    plt.title("U.S. Wind Potential Map (Station-Level Average Wind Speed)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.clim(0, 12)

    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Wrote figure to {output_path}")


if __name__ == "__main__":
    plot_us_wind_station_map()