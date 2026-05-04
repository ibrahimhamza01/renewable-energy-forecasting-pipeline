# Model Selection: Wind Capacity Factor Forecasting

## 1. Objective

The objective of this phase is to identify the best-performing model for forecasting:

**Target:** `next_day_daily_region_capacity_factor`  
**Horizon:** 1 day ahead  

The selected model should:
- Minimize prediction error (RMSE, MAE)
- Generalize well to unseen data
- Capture temporal and weather-driven dynamics

---

## 2. Dataset Overview

| Split        | Rows     |
|-------------|----------|
| Train       | ~390k    |
| Validation  | ~100k    |
| Test        | 46,507   |

Final model training strategy:
> Train on **Train + Validation**, evaluate on **Test**

---

## 3. Models Evaluated

The following models were evaluated:

### 3.1 Baseline Models
- Naive / persistence-style features (via lag features)

### 3.2 Linear Regression
- Captures linear relationships
- Fast and interpretable
- Limited ability to model nonlinear patterns

### 3.3 Random Forest Regressor
- Ensemble of decision trees
- Captures nonlinearities
- Robust but less sensitive to temporal trends

### 3.4 Gradient Boosted Trees (GBT)
- Sequential tree boosting
- Strong performance on structured/tabular data
- Handles nonlinearities and interactions effectively

---

## 4. Hyperparameter Tuning (GBT)

Grid search was conducted over:

- `max_iter`: [30, 50, 80]
- `max_depth`: [3, 5, 7]
- `step_size`: [0.05, 0.1]

### Best Configuration

```json
{
  "max_iter": 80,
  "max_depth": 5,
  "step_size": 0.05,
  "seed": 42
}
````

Validation performance (best run):

* RMSE ≈ **0.04650**
* MAE ≈ **0.02717**

---

## 5. Final Model Training

The final model was trained using:

* **Train + Validation data**
* Best hyperparameters from tuning

---

## 6. Test Set Performance

| Metric | Value       |
| ------ | ----------- |
| RMSE   | **0.04202** |
| MAE    | **0.02566** |

### Interpretation

* Lower RMSE than validation → good generalization
* Stable MAE → consistent prediction quality
* Indicates strong model fit without overfitting

---

## 7. Feature Importance Analysis

Top contributing features:

| Feature                                         | Importance |
| ----------------------------------------------- | ---------- |
| `daily_region_capacity_factor`                  | 0.244      |
| `day_of_year`                                   | 0.084      |
| `avg_station_wind_speed_std_ms`                 | 0.082      |
| `daily_region_capacity_factor_rolling_30d_mean` | 0.082      |
| `state_long_run_volatility`                     | 0.057      |
| `state_long_run_avg_cf`                         | 0.054      |
| `cf_lag_1d`                                     | 0.048      |
| `mean_region_wind_speed_ms`                     | 0.042      |

### Key Insights

* **Strong temporal dependence**

  * Lag features and rolling statistics dominate
* **Seasonality matters**

  * `day_of_year`, `month` are important
* **Wind variability is critical**

  * Standard deviation and range features are highly influential
* **Long-term state behavior matters**

  * Historical averages and volatility improve predictions

---

## 8. Model Selection Decision

### Selected Model: **Gradient Boosted Trees (GBT)**

**Reasons:**

* Best performance (lowest RMSE and MAE)
* Captures nonlinear relationships effectively
* Handles temporal + weather feature interactions
* Robust across training and test datasets

---

## 9. Model Registration

Registered model:

```text
Model Name: final_tuned_gbt
Version ID: final_tuned_gbt_20260504T063157Z
Status: production_candidate
```

Stored in:

```text
s3a://syed-datsbd-s2026/models/registry/
```

Includes:

* Model artifact
* Hyperparameters
* Metrics
* Feature importance
* Training configuration

---

## 10. Conclusion

The Gradient Boosted Trees model provides:

* High predictive accuracy
* Strong generalization to unseen data
* Meaningful feature interpretability

It is selected as the **production candidate model** for next-day wind capacity factor forecasting.

---

## 11. Next Steps

* Deploy inference pipeline
* Build forecast generation scripts
* Monitor model performance over time
* Evaluate multi-day forecasting horizons