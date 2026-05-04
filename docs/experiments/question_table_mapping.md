# Question → Table Mapping (Wind Energy Pipeline)

This document maps key project questions to the datasets and methods used to answer them.

It ensures that every analytical claim is grounded in the correct data layer.

---

## 1. Where is wind potential strongest?

**Table used:**

* `gold_monthly_state_wind`

**Why this table:**

* Aggregated at **state-month level**
* Smooths daily noise
* Suitable for long-run comparisons

**Method:**

* Compute average `monthly_region_capacity_factor` per state
* Rank states

**Insight:**

* Great Plains (ND, SD, KS, NE) dominate wind potential
* Southeast shows consistently low wind potential

---

## 2. How does wind potential vary over time?

**Table used:**

* `gold_monthly_state_wind`

**Why this table:**

* Monthly aggregation reveals **seasonality**

**Method:**

* Group by `month`
* Compute average capacity factor

**Insight:**

* Strong seasonal pattern
* Peak: winter / early spring
* Lowest: summer

---

## 3. Which regions have more stable wind patterns?

**Table used:**

* `gold_daily_region_wind`

**Why this table:**

* Daily granularity captures variability

**Method:**

* Compute:

  * mean capacity factor
  * standard deviation
  * coefficient of variation

**Insight:**

* High-wind states are **more stable relative to their mean**
* Low-wind states show **higher relative variability**

---

## 4. What are extreme wind events?

**Table used:**

* `gold_extreme_event_windows`

**Why this table:**

* Explicitly engineered for anomaly detection

**Method:**

* State-level thresholds:

  * bottom 10% → low wind
  * top 10% → high wind
* Z-score normalization

**Insight:**

* ~10% high wind, ~10% low wind
* Extreme events are rare but significant
* Critical for grid stress and forecasting

---

## 5. What is wind potential?

**Tables used:**

* `gold_daily_region_wind`
* `gold_monthly_state_wind`

**Definition:**
Wind potential is measured using **capacity factor**, defined as:

> normalized wind energy output (0 to 1)

**Interpretation:**

* 0 → no usable wind
* ~0.05 → low/moderate wind
* ~0.1+ → strong wind
* ~0.3+ → very strong conditions

---

## 6. How stable is wind energy overall?

**Table used:**

* `gold_daily_region_wind`

**Method:**

* Distribution analysis (histogram + box plot)

**Insight:**

* Highly **right-skewed distribution**
* Most days → low/moderate wind
* Rare extreme spikes

---

## 7. What time scale is most useful?

**Tables compared:**

* Hourly (silver / intermediate)
* Daily (`gold_daily_region_wind`)
* Monthly (`gold_monthly_state_wind`)

**Conclusion:**

| Time Scale | Use Case                     |
| ---------- | ---------------------------- |
| Hourly     | Too noisy                    |
| Daily      | Best for modeling + analysis |
| Monthly    | Best for storytelling        |

---

## 8. What does this mean in the real world?

**Implications:**

* Wind energy is **location-dependent**
* It is **seasonal and predictable**
* It is **not constant → requires forecasting**
* Extreme events matter for:

  * grid stability
  * energy planning

---

## Final Summary

The pipeline produces structured datasets that allow us to:

* understand wind behavior across time and geography
* quantify variability and extremes
* support forecasting and decision-making

All insights are grounded in **validated Gold tables built from real NOAA data**.
