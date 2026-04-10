from pathlib import Path

from src.common.config import config


class Paths:
    def __init__(self):
        self.project_root = config.project_root

        self.local_data_root = Path(config.runtime["local_data_root"])
        self.local_output_root = Path(config.runtime["local_output_root"])

        self.aws_bucket = config.aws["s3_bucket"]

        self._logical_paths = config.paths

    def _local_path(self, relative_path: str) -> str:
        return str(self.local_data_root / relative_path)

    def _output_path(self, relative_path: str) -> str:
        return str(self.local_output_root / Path(relative_path).name)

    def _s3_path(self, relative_path: str) -> str:
        return f"s3://{self.aws_bucket}/{relative_path}"

    @property
    def raw_isd(self) -> str:
        return self._s3_path(self._logical_paths["data"]["raw_isd"])

    @property
    def bronze_isd(self) -> str:
        return self._s3_path(self._logical_paths["bronze"]["isd"])

    @property
    def silver_weather(self) -> str:
        return self._s3_path(self._logical_paths["silver"]["weather"])

    @property
    def gold_wind_station_hourly(self) -> str:
        return self._s3_path(self._logical_paths["gold"]["wind_station_hourly"])

    @property
    def gold_wind_station_daily(self) -> str:
        return self._s3_path(self._logical_paths["gold"]["wind_station_daily"])

    @property
    def gold_wind_region_daily(self) -> str:
        return self._s3_path(self._logical_paths["gold"]["wind_region_daily"])

    @property
    def gold_wind_region_monthly(self) -> str:
        return self._s3_path(self._logical_paths["gold"]["wind_region_monthly"])

    @property
    def model_registry(self) -> str:
        return self._s3_path(self._logical_paths["models"]["registry"])

    @property
    def forecast_outputs(self) -> str:
        return self._s3_path(self._logical_paths["forecasts"]["outputs"])

    @property
    def benchmark_results(self) -> str:
        return self._s3_path(self._logical_paths["benchmarks"]["results"])

    @property
    def output_figures(self) -> str:
        return self._output_path(self._logical_paths["outputs"]["figures"])

    @property
    def output_metrics(self) -> str:
        return self._output_path(self._logical_paths["outputs"]["metrics"])

    @property
    def output_sample_runs(self) -> str:
        return self._output_path(self._logical_paths["outputs"]["sample_runs"])


paths = Paths()
