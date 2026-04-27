import os
import glob
import subprocess
import pandas as pd
import matplotlib.pyplot as plt

BUCKET = "alejandrog-alt-datsbd-s2026"
S3_BASE = f"s3://{BUCKET}/outputs/eda_gold_questions"
LOCAL_DIR = "outputs/eda_gold_questions_local"
CHART_DIR = "outputs/eda_charts"

os.makedirs(LOCAL_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

outputs = {
    "q1": "q1_strongest_wind_by_state",
    "q2": "q2_seasonal_wind_by_month",
    "q2_top": "q2_top_months_by_state",
    "q3": "q3_stability_by_state",
    "q4": "q4_qc_data_coverage",
    "q4_summary": "q4_qc_summary",
    "q5": "q5_timescale_comparison",
}


def download_folder(name):
    s3_path = f"{S3_BASE}/{name}/"
    local_path = f"{LOCAL_DIR}/{name}"
    os.makedirs(local_path, exist_ok=True)

    subprocess.run(
        ["aws", "s3", "cp", s3_path, local_path, "--recursive", "--exclude", "_SUCCESS"],
        check=True
    )

    csv_files = glob.glob(f"{local_path}/*.csv")
    if not csv_files:
        raise FileNotFoundError(f"No CSV found for {name}")

    return pd.read_csv(csv_files[0])


def save_and_show(filename):
    plt.tight_layout()
    plt.savefig(f"{CHART_DIR}/{filename}", dpi=300)
    plt.show()
    plt.close()


def bar_chart(df, x, y, title, ylabel, filename):
    plt.figure(figsize=(9, 5))
    plt.bar(df[x], df[y])
    plt.title(title, fontsize=14)
    plt.xlabel(x)
    plt.ylabel(ylabel)
    plt.grid(axis="y", alpha=0.3)
    save_and_show(filename)


print("Downloading EDA outputs from S3...")

q1 = download_folder(outputs["q1"])
q2 = download_folder(outputs["q2"])
q2_top = download_folder(outputs["q2_top"])
q3 = download_folder(outputs["q3"])
q4 = download_folder(outputs["q4"])
q4_summary = download_folder(outputs["q4_summary"])
q5 = download_folder(outputs["q5"])

print("Creating and displaying charts...")

# Q1
q1 = q1.sort_values("avg_capacity_factor", ascending=False)

bar_chart(
    q1,
    "state",
    "avg_capacity_factor",
    "Q1: Average Capacity Factor by State",
    "Average Capacity Factor",
    "q1_capacity_factor_by_state.png"
)

bar_chart(
    q1,
    "state",
    "avg_power_density_wm2",
    "Q1: Average Wind Power Density by State",
    "Average Power Density (W/m²)",
    "q1_power_density_by_state.png"
)

# Q2
plt.figure(figsize=(10, 6))
for state in q2["state"].unique():
    temp = q2[q2["state"] == state].sort_values("month")
    plt.plot(temp["month"], temp["avg_capacity_factor"], marker="o", label=state)

plt.title("Q2: Seasonal Wind Potential by State", fontsize=14)
plt.xlabel("Month")
plt.ylabel("Average Capacity Factor")
plt.xticks(range(1, 13))
plt.grid(alpha=0.3)
plt.legend(title="State")
save_and_show("q2_seasonal_capacity_factor.png")

plt.figure(figsize=(10, 6))
for state in q2["state"].unique():
    temp = q2[q2["state"] == state].sort_values("month")
    plt.plot(temp["month"], temp["avg_wind_speed_ms"], marker="o", label=state)

plt.title("Q2: Seasonal Average Wind Speed by State", fontsize=14)
plt.xlabel("Month")
plt.ylabel("Average Wind Speed (m/s)")
plt.xticks(range(1, 13))
plt.grid(alpha=0.3)
plt.legend(title="State")
save_and_show("q2_seasonal_wind_speed.png")

# Q3
q3 = q3.sort_values("coefficient_of_variation")

bar_chart(
    q3,
    "state",
    "coefficient_of_variation",
    "Q3: Wind Stability by State",
    "Coefficient of Variation (Lower = More Stable)",
    "q3_wind_stability_by_state.png"
)

bar_chart(
    q3.sort_values("std_daily_wind_speed_ms"),
    "state",
    "std_daily_wind_speed_ms",
    "Q3: Daily Wind Speed Variability by State",
    "Std Dev of Daily Wind Speed",
    "q3_daily_wind_std_by_state.png"
)

# Q4
q4_total = (
    q4.groupby("state", as_index=False)
    .agg({
        "station_day_rows": "sum",
        "station_count": "max",
        "total_observations_after_qc": "sum"
    })
    .sort_values("total_observations_after_qc", ascending=False)
)

bar_chart(
    q4_total,
    "state",
    "total_observations_after_qc",
    "Q4: Observations Remaining After Quality Control",
    "Hourly Observations After QC",
    "q4_observations_after_qc_by_state.png"
)

plt.figure(figsize=(10, 6))
for state in q4["state"].unique():
    temp = q4[q4["state"] == state].sort_values("year")
    plt.plot(temp["year"], temp["total_observations_after_qc"], marker="o", label=state)

plt.title("Q4: QC Data Coverage by Year and State", fontsize=14)
plt.xlabel("Year")
plt.ylabel("Observations After QC")
plt.xticks(sorted(q4["year"].unique()))
plt.grid(alpha=0.3)
plt.legend(title="State")
save_and_show("q4_qc_coverage_by_year_state.png")

# Q5
q5 = q5.sort_values("time_scale")

bar_chart(
    q5,
    "time_scale",
    "std_wind_speed_ms",
    "Q5: Wind Speed Variability by Time Scale",
    "Standard Deviation of Wind Speed",
    "q5_variability_by_timescale.png"
)

bar_chart(
    q5,
    "time_scale",
    "rows",
    "Q5: Data Volume by Time Scale",
    "Number of Rows",
    "q5_rows_by_timescale.png"
)

# Answers
strongest = q1.iloc[0]
most_stable = q3.iloc[0]
most_data = q4_total.iloc[0]

answers = f"""
EDA ANSWERS FOR PRESENTATION
============================

Q1. Where is wind potential strongest?
{strongest['state']} has the strongest wind potential. It has the highest average capacity factor
({strongest['avg_capacity_factor']}) and the highest average wind power density
({strongest['avg_power_density_wm2']} W/m²).

Q2. How does wind potential vary by season?
Wind potential varies by month and state. The seasonal charts show when each state reaches
its strongest capacity factor and wind speed.

Top months by state:
{q2_top.to_string(index=False)}

Q3. Which regions have more stable wind patterns?
{most_stable['state']} has the most stable wind pattern based on the lowest coefficient
of variation ({most_stable['coefficient_of_variation']}).

Q4. How much data remains after quality control?
A large amount of usable data remains after QC. The state with the most remaining observations
is {most_data['state']}, with {int(most_data['total_observations_after_qc']):,} hourly observations.

QC summary:
{q4_summary.to_string(index=False)}

Q5. What time scale is most useful?
Daily data is the best balance for EDA and forecasting. Hourly data is detailed but noisy.
Monthly data is useful for long-term seasonal planning but hides short-term variation.

Generated charts are saved in:
{CHART_DIR}
"""

with open(f"{CHART_DIR}/eda_presentation_answers.txt", "w") as f:
    f.write(answers)

print(answers)
print(f"\nCharts saved to: {CHART_DIR}")