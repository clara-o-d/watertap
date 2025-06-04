'''
Task: Create a simple flowsheet using the zero-order evaporation pond unit model
'''
# imports
import os
import idaes.logger as idaeslog
from pyomo.environ import (
    assert_optimal_termination,
    ConcreteModel,
    Block,
    Expression,
    Objective,
    value,
    TransformationFactory,
    units as pyunits,
)
from pyomo.network import Arc, SequentialDecomposition
from pyomo.util.check_units import assert_units_consistent

from idaes.core import (
    FlowsheetBlock,
    MomentumBalanceType,
    UnitModelBlockData,
    UnitModelCostingBlock
)

from watertap.core.solvers import get_solver
from idaes.core.util.initialization import propagate_state

import idaes.core.util.scaling as iscale

from watertap.core.util.initialization import assert_degrees_of_freedom
from watertap.core.wt_database import Database
from watertap.core.zero_order_properties import WaterParameterBlock
from watertap.unit_models.zero_order import (
    FeedZO,
    EvaporationPondZO
)

from watertap.costing.zero_order_costing import ZeroOrderCosting
from watertap.costing import WaterTAPCosting

# logger
_log = idaeslog.getLogger(__name__)

# main
def main():
    m = build()
    set_operating_conditions(m)

    assert_units_consistent(m)

    initialize_system(m)
    m.display()
    print('____________________________________________________________________________')
    # assert_degrees_of_freedom(m, 0)

    results = solve(m, checkpoint="solve flowsheet after initializing system")
    assert_optimal_termination(results)
    m.fs.pond.report()
    add_costing(m)
    # initialize_costing(m)

    # optimize_operation(m)
    # results = solve(m, checkpoint="solve flowsheet after costing")
    # assert_optimal_termination(results)

    # display_results(m)

# build
def build():
    # flowsheet set up
    m = ConcreteModel()
    m.db = Database()

    m.fs = FlowsheetBlock(dynamic=False)
    m.fs.params = WaterParameterBlock(
        solute_list=["tds", "lithium", "chlorine", "sodium", "potassium", "magnesium", "calcium", "sulfate"]
    )

    # define flowsheet inlets and outlets
    m.fs.feed = FeedZO(property_package = m.fs.params)
    m.fs.pond = EvaporationPondZO(property_package = m.fs.params, database = m.db)

    # connections
    m.fs.s_feed = Arc(source=m.fs.feed.outlet, destination=m.fs.pond.inlet)
    TransformationFactory("network.expand_arcs").apply_to(m) # Could this be re-explained...?

    # scaling

    # set unit model values

    # m.display()
    return m

# set operating conditions
def set_operating_conditions(m):
    # feed
    flow_vol = 280 / 3600 * pyunits.m**3 / pyunits.s
    conc_mass_tds = 290 * pyunits.kg / pyunits.m**3
    conc_mass_li = 1 * pyunits.kg / pyunits.m**3
    conc_mass_cl = 200 * pyunits.kg / pyunits.m**3
    conc_mass_na = 60 * pyunits.kg / pyunits.m**3
    conc_mass_k = 10 * pyunits.kg / pyunits.m**3
    conc_mass_mg = 15 * pyunits.kg / pyunits.m**3
    conc_mass_ca = 2 * pyunits.kg / pyunits.m**3
    conc_mass_so4 = 2 * pyunits.kg / pyunits.m**3

    m.fs.feed.flow_vol[0].fix(flow_vol)
    m.fs.feed.conc_mass_comp[0, "tds"].fix(conc_mass_tds)
    m.fs.feed.conc_mass_comp[0, "lithium"].fix(conc_mass_li)
    m.fs.feed.conc_mass_comp[0, "chlorine"].fix(conc_mass_cl)
    m.fs.feed.conc_mass_comp[0, "sodium"].fix(conc_mass_na)
    m.fs.feed.conc_mass_comp[0, "potassium"].fix(conc_mass_k)
    m.fs.feed.conc_mass_comp[0, "magnesium"].fix(conc_mass_mg)
    m.fs.feed.conc_mass_comp[0, "calcium"].fix(conc_mass_ca)
    m.fs.feed.conc_mass_comp[0, "sulfate"].fix(conc_mass_so4)
    solve(m.fs.feed, checkpoint="solve feed block")

    # evaporation pond
    m.fs.pond.load_parameters_from_database(use_default_removal=True)
    # print('------------------------------------------------------------------------------------')
    # m.display()

# initialize the system
def initialize_system(m):
    propagate_state(m.fs.s_feed)
    seq = SequentialDecomposition()
    seq.options.tear_set = []
    seq.options.iterLim = 1

    seq.run(m.fs.pond, lambda u: u.initialize())

    # print('------------------------------------------------------------------------------------')
    # m.display()

# # optimize the operation
# def optimize_operation():
#     pass

# solve the flowsheet
def solve(blk, solver=None, checkpoint=None, tee=False, fail_flag=True):
    if solver is None:
        solver = get_solver()
    results = solver.solve(blk, tee=tee)
    return results

# add costing
def add_costing(m):
    m.fs.costing = ZeroOrderCosting()
    m.fs.costing.base_currency = pyunits.USD_2023 # change to 2025?
    m.fs.pond.costing = UnitModelCostingBlock(flowsheet_costing_block=m.fs.costing)
    
    assert_units_consistent(m)
    print(m.fs.pond.costing.capital_cost.value)

# # initialize the costing
# def initialize_costing():
#     pass

if __name__ == "__main__":
    main()