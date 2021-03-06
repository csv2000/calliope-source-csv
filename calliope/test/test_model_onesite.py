import pytest
import tempfile

from calliope.utils import AttrDict
from . import common
from .common import assert_almost_equal, solver


class TestModel:
    @pytest.fixture(scope='module')
    def model(self):
        locations = """
            locations:
                1:
                    techs: ['ccgt', 'demand_power']
                    override:
                        ccgt:
                            constraints:
                                e_cap.max: 100
                        demand_power:
                            constraints:
                                r: -50
            links:
        """
        config_run = """
            mode: plan
            model: [{techs}, {locations}]
            subset_t: ['2005-01-01', '2005-01-02']
        """
        with tempfile.NamedTemporaryFile() as f:
            f.write(locations.encode('utf-8'))
            f.read()
            model = common.simple_model(config_run=config_run,
                                        config_locations=f.name,
                                        override=AttrDict({'solver': solver}))
        model.run()
        return model

    def test_model_solves(self, model):
        assert str(model.results.solver.termination_condition) == 'optimal'

    def test_model_balanced(self, model):
        sol = model.solution
        assert sol['e'].loc[dict(c='power', y='ccgt')].sum(dim='x').mean() == 50
        assert (sol['e'].loc[dict(c='power', y='ccgt')].sum(dim='x') ==
                -1 * sol['e'].loc[dict(c='power', y='demand_power')].sum(dim='x')).all()

    def test_model_costs(self, model):
        sol = model.solution
        assert_almost_equal(sol['summary'].to_pandas().loc['ccgt', 'levelized_cost_monetary'], 0.1)
