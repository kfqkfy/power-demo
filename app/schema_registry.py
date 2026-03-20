SCHEMA_REGISTRY = {
    "energy": {
        "table": "energy_daily",
        "date_field": "stat_date",
        "joins": [
            {
                "table": "dim_station_area sa",
                "on": "energy_daily.station_area_id = sa.station_area_id"
            }
        ],
        "entity_fields": {
            "station_area": "sa.station_area_name",
            "power_station": "sa.power_station_name",
            "line": "sa.line_name"
        },
        "region_field": "sa.region_name",
        "metric_fields": {
            "energy": "energy_daily.energy_kwh"
        }
    },
    "load": {
        "table": "load_daily",
        "date_field": "stat_date",
        "joins": [
            {
                "table": "dim_station_area sa",
                "on": "load_daily.station_area_id = sa.station_area_id"
            }
        ],
        "entity_fields": {
            "station_area": "sa.station_area_name",
            "power_station": "sa.power_station_name",
            "line": "sa.line_name"
        },
        "region_field": "sa.region_name",
        "metric_fields": {
            "max_load": "load_daily.max_load_kw",
            "avg_load": "load_daily.avg_load_kw"
        }
    },
    "line_loss": {
        "table": "line_loss_daily",
        "date_field": "stat_date",
        "joins": [
            {
                "table": "dim_station_area sa",
                "on": "line_loss_daily.station_area_id = sa.station_area_id"
            }
        ],
        "entity_fields": {
            "station_area": "sa.station_area_name",
            "power_station": "sa.power_station_name",
            "line": "sa.line_name"
        },
        "region_field": "sa.region_name",
        "metric_fields": {
            "line_loss_rate": "line_loss_daily.line_loss_rate"
        }
    }
}
