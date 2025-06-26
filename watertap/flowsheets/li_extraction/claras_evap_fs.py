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
from idaes.core.util import DiagnosticsToolbox
from idaes.core.util import model_statistics as istat

# logger
_log = idaeslog.getLogger(__name__)

# main
def main():
    m = build()
    set_operating_conditions(m)
    
    dt = DiagnosticsToolbox(m)
    dt.report_structural_issues()

    assert_degrees_of_freedom(m, 0)
    # assert_units_consistent(m)

    # initialize_system(m)
    # m.display()
    # print('____________________________________________________________________________')
    # assert_degrees_of_freedom(m, 0)

    results = solve(m, checkpoint="solve flowsheet after initializing system")
    # assert_optimal_termination(results)
    # m.fs.pond.report()
    add_costing(m)
    initialize_costing(m)

    # optimize_operation(m)
    results = solve(m, checkpoint="solve flowsheet after costing")
    m.fs.pond.costing.display()
    print(f"Air temperature: {m.fs.pond.air_temperature[0].value}")
    # lcoli = value(pyunits.convert(m.fs.LCOLi, to_units=pyunits.USD_2023 / pyunits.tonne))
    # print("lcoli: " + str(lcoli)) # m, results
    # assert_optimal_termination(results)

    # display_results(m)

# build
def build():
    # flowsheet set up
    m = ConcreteModel()

    path = os.getcwd()
    m.db = Database(dbpath=path)

    m.fs = FlowsheetBlock(dynamic=False)
    m.fs.params = WaterParameterBlock(
        solute_list=["lithium", "potassium", "magnesium", "calcium"]
    )

    # define flowsheet inlets and outlets
    m.fs.pond = EvaporationPondZO(property_package = m.fs.params, database = m.db)

    # connections

    # scaling

    # set unit model values

    # m.display()
    return m

# set operating conditions
def set_operating_conditions(m):
    m.fs.pond.inlet.flow_mass_comp[0, "H2O"].fix(1013.931)
    m.fs.pond.inlet.flow_mass_comp[0, "lithium"].fix(1.65)
    m.fs.pond.inlet.flow_mass_comp[0, "potassium"].fix(24.804)
    m.fs.pond.inlet.flow_mass_comp[0, "magnesium"].fix(10.142)
    m.fs.pond.inlet.flow_mass_comp[0, "calcium"].fix(0.473)

    m.fs.pond.load_parameters_from_database(use_default_removal=True)
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
    m.fs.pond.costing = UnitModelCostingBlock(flowsheet_costing_block=m.fs.costing)

    # @m.fs.Expression(
    #     doc="Levelized cost of lithium product"
    # )
    # def LCOLi(b):
    #     return (
    #         b.pond.costing.capital_cost * b.costing.capital_recovery_factor
    #     ) / (
    #         pyunits.convert(
    #             b.pond.treated.flow_mass_comp[0, "lithium"],
    #             to_units=pyunits.tonne / pyunits.year,
    #         )
    #         * b.costing.utilization_factor
    #     )
    # m.fs.costing.cost_process() # error here
    # m.fs.costing.aggregate_costs()
    # m.fs.costing.add_LCOW(m.fs.pond.inlet.flow_mass_comp[0, "lithium"], name="LCOLi")
    
    assert_units_consistent(m)

# initialize the costing
def initialize_costing(m):
    m.fs.pond.costing.initialize()

if __name__ == "__main__":
    main()