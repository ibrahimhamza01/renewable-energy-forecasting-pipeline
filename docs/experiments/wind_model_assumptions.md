## Validation Results

### Local Unit Test Validation

Layer 6 Part A was validated locally using the wind power curve unit test suite.

Result:

```text
23 passed
````

This confirms:

* cut-in, rated, and cut-out behavior works correctly
* normalized power stays within the expected range
* null wind speeds return null
* negative wind speeds return null
* wind power density is computed correctly
* capacity factor aggregation works
* wind power class assignment works

### Local Spark Sanity Test

A local Spark sanity test was run using synthetic wind speeds:

```text
0.0, 3.5, 6.0, 13.0, 20.0, 30.0, null, -1.0
```

Observed behavior:

| Wind speed | Normalized power | Interpretation          |
| ---------: | ---------------: | ----------------------- |
|        0.0 |              0.0 | no wind                 |
|        3.5 |              0.0 | cut-in threshold        |
|        6.0 |         0.080369 | cubic ramp region       |
|       13.0 |              1.0 | rated output            |
|       20.0 |              1.0 | rated-to-cut-out region |
|       30.0 |              0.0 | above cut-out shutdown  |
|       null |             null | missing input           |
|       -1.0 |             null | invalid physical value  |

### EC2 Spark Cluster Smoke Test

The wind power curve was also tested using `spark-submit` on the EC2 Spark cluster.

Spark master:

```text
spark://ip-172-31-83-109.ec2.internal:7077
```

Cluster state during validation:

```text
Alive workers: 4
Total cores: 8
Total memory: 26.5 GiB
```

The synthetic Spark smoke test completed successfully and produced expected normalized power and wind power density values.

### Real Silver Data Smoke Test

A real Silver-table smoke test was run against the configured Silver dataset path.

The path was resolved from user config:

```text
configs/users/syed.yaml
```

Logical source:

```text
aws.project_bucket + aws.silver_prefix
```

Resolved source:

```text
s3a://syed-datsbd-s2026/silver/weather
```

The test intentionally used a sample of 10,000 non-null wind-speed rows from Silver:

```python
.limit(10000)
```

This was not a full Silver production run. The goal was to confirm that the Layer 6 Part A wind power logic is compatible with the actual Silver schema and Spark/S3 runtime.

Silver schema note:

```text
timestamp_utc
```

is the correct Silver timestamp column.

### Real Silver Sample Results

Summary over 10,000 sampled Silver rows:

| Metric                    |        Value |
| ------------------------- | -----------: |
| Rows tested               |       10,000 |
| Minimum wind speed        |      0.0 m/s |
| Maximum wind speed        |     20.1 m/s |
| Minimum normalized power  |          0.0 |
| Maximum normalized power  |          1.0 |
| Average normalized power  | 0.1046124419 |
| Bad normalized power rows |            0 |

Validation check:

```text
bad_normalized_power_rows=0
```

This confirms that normalized power stayed within the expected `[0, 1]` range on real Silver data.

Completion evidence:

* wind power curve implementation exists
* config file exists
* assumptions document exists
* local tests passed
* local Spark sanity test passed
* EC2 Spark synthetic smoke test passed
* EC2 Spark real Silver sample smoke test passed
* no invalid normalized power values were found in the Silver sample

