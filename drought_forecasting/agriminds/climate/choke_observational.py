"""
Compatibility layer redirecting to Abergelle - Tekeze Basin Observational Climate Engine.
All Choke observational endpoints have been pivoted to Abergelle - Tekeze Basin.
"""

from agriminds.climate.tekeze_abergelle_observational import (
    get_grid_spec,
    get_grid_mask,
    load_climate_cube,
    get_latest_tekeze_grid_state as get_latest_choke_grid_state,
    get_latest_tekeze_grid_state,
    get_cell_observational_history,
    get_basin_timeseries_df,
)

__all__ = [
    "get_grid_spec",
    "get_grid_mask",
    "load_climate_cube",
    "get_latest_choke_grid_state",
    "get_latest_tekeze_grid_state",
    "get_cell_observational_history",
    "get_basin_timeseries_df",
]
