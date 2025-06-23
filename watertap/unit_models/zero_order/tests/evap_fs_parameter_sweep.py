import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyomo.environ as pyo
from idaes.core.util.model_statistics import degrees_of_freedom
from parameter_sweep import ParameterSweep, LinearSample, NormalSample
from pyomo.util.check_units import assert_units_consistent
from idaes.core.solvers import get_solver

from claras_evap_fs import build, set_operating_conditions, solve, add_costing, initialize_costing

# initial solve
m = build()
set_operating_conditions(m)
solve(m)
add_costing(m)
initialize_costing(m)

# Parameters to sweep
flow_vol     = m.fs.feed.flow_vol[0] 
conc_Li      = m.fs.feed.conc_mass_comp[0, 'lithium'] 
conc_Cl      = m.fs.feed.conc_mass_comp[0, 'chlorine'] 
solar_radiation = m.fs.pond.solar_radiation[0]
land_cost     = m.fs.costing.evaporation_pond.land_cost[None]
liner_thick   = m.fs.costing.evaporation_pond.liner_thickness[None]

# Set ranges
sweep_params = {
    'flow vol (m^3/h)'  : LinearSample(flow_vol, 100, 400, 4), 
    'Li (kg/m^3)'    : LinearSample(conc_Li,  0.5,  5.0, 4), 
    'solar radiation (mJ/m^2)' : LinearSample(solar_radiation, 10, 30, 4),
    'land cost' : LinearSample(land_cost,   3_000, 7_000, 4),
    'liner thickness (mm)' : LinearSample(liner_thick, 50, 60, 4)
}

# Outputs
outputs = {
    'area'   : m.fs.pond.area[0],
    'capex'     : m.fs.pond.costing.capital_cost
}


# Perform sweep
ps = ParameterSweep(
    optimize_function = solve,
    csv_results_file_name = 'pond_sensitivity.csv'
)

ps.parameter_sweep(
    build_model        = m,
    build_sweep_params = sweep_params,
    build_outputs      = outputs,
)