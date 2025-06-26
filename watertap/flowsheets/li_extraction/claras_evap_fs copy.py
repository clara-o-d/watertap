import idaes.logger as idaeslog
from pyomo.environ import (
    ConcreteModel,
)
from idaes.core import FlowsheetBlock, UnitModelCostingBlock
from watertap.core.solvers import get_solver
from watertap.core.wt_database import Database
from watertap.core.zero_order_properties import WaterParameterBlock
from watertap.unit_models.zero_order import FeedZO, EvaporationPondZO
from idaes.core.util.model_diagnostics import DiagnosticsToolbox
from watertap.costing.zero_order_costing import ZeroOrderCosting
import os

# logger
_log = idaeslog.getLogger(__name__)


# main
def main():
    m = build()
    set_operating_conditions(m)
    add_costing(m)
    m.fs.costing.pprint()
    m.fs.costing.cost_process()
    print(f"Air temperature: {m.fs.pond.air_temperature[0].value}")


# build
def build():
    m = ConcreteModel()
    path = os.getcwd()
    m.db = Database(dbpath=path)
    m.fs = FlowsheetBlock(dynamic=False)
    m.fs.params = WaterParameterBlock(
        solute_list=["tds", "magnesium", "calcium", "nitrate", "sulfate", "tss"]
    )
    m.fs.pond = EvaporationPondZO(property_package=m.fs.params, database=m.db)
    return m


# set operating conditions
def set_operating_conditions(m):
    # feed
    m.fs.pond.inlet.flow_mass_comp[0, "H2O"].fix(10)
    m.fs.pond.inlet.flow_mass_comp[0, "tds"].fix(123)
    m.fs.pond.inlet.flow_mass_comp[0, "magnesium"].fix(456)
    m.fs.pond.inlet.flow_mass_comp[0, "calcium"].fix(789)
    m.fs.pond.inlet.flow_mass_comp[0, "nitrate"].fix(10)
    m.fs.pond.inlet.flow_mass_comp[0, "sulfate"].fix(11)
    m.fs.pond.inlet.flow_mass_comp[0, "tss"].fix(12)

    m.fs.pond.load_parameters_from_database(use_default_removal=True)


# solve the flowsheet
def solve(blk, solver=None, checkpoint=None, tee=False, fail_flag=True):
    if solver is None:
        solver = get_solver()
    results = solver.solve(blk, tee=tee)
    return results


def add_costing(m):
    m.fs.costing = ZeroOrderCosting()
    m.fs.pond.costing = UnitModelCostingBlock(flowsheet_costing_block=m.fs.costing)


def run_diagnostics(m):
    dt = DiagnosticsToolbox(m)
    dt.report_structural_issues()
    dt.display_underconstrained_set()
    dt.display_potential_evaluation_errors()
    m.fs.pond.initialize()
    dt.report_numerical_issues()


if __name__ == "__main__":
    main()