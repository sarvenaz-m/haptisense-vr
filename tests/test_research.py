import json
import math
import random
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from haptisense.research import ResearchConfig, ResearchContact, run_research, write_research
from haptisense.identification import fit_kelvin, evaluate_fit

ROOT = Path(__file__).resolve().parents[1]


class ResearchMechanicsTests(unittest.TestCase):
    def test_elastic_analytical_value(self):
        c = ResearchConfig(model="elastic", stiffness=500, nonlinear=10000)
        r = ResearchContact(c).step(.004, .02, 0)
        self.assertAlmostEqual(r["normal_n"], 500*(.004+10000*.004**3), places=12)
        self.assertEqual(r["memory_n"], 0)

    def test_exact_memory_decay_at_fixed_depth(self):
        c = ResearchConfig(tau=.2, nonlinear=0)
        model = ResearchContact(c)
        for _ in range(50):
            model.step(.004, .01, 0)
        initial = model.memory
        for _ in range(100):
            result = model.step(.004, 0, 0)
        self.assertAlmostEqual(result["memory_n"], initial*math.exp(-1), places=12)
        self.assertAlmostEqual(result["normal_n"], c.stiffness*.004+initial*math.exp(-1), places=12)

    def test_kelvin_is_approach_only(self):
        c = ResearchConfig(model="kelvin", nonlinear=0)
        a = ResearchContact(c).step(.003, .02, 0)
        b = ResearchContact(c).step(.003, -.02, 0)
        self.assertAlmostEqual(a["normal_n"]-b["normal_n"], c.damping*.02)

    def test_friction_dissipates_for_both_directions(self):
        for speed in (-.2, -.004, 0, .004, .2):
            r = ResearchContact(ResearchConfig()).step(.003, 0, speed)
            self.assertLessEqual(r["friction_n"]*speed, 0)
            self.assertLessEqual(abs(r["friction_n"]), .18*r["normal_n"]+1e-12)

    def test_release_clears_memory_and_command(self):
        m = ResearchContact(ResearchConfig())
        m.step(.005, .05, .05)
        r = m.step(0, -.1, .05)
        self.assertEqual(r["command_n"], 0)
        self.assertEqual(r["memory_n"], 0)
        self.assertEqual(r["amplitude"], 0)

    def test_invalid_input_resets_state(self):
        m = ResearchContact(ResearchConfig())
        m.step(.005, .05, 0)
        with self.assertRaises(ValueError):
            m.step(float('nan'), 0, 0)
        self.assertEqual(m.memory, 0)
        self.assertEqual(m.previous, (0, 0))

    def test_limits_over_high_load_run(self):
        c = ResearchConfig(stiffness=4000, depth=.01, force_limit=3, slew_limit=50)
        result = run_research(c, "cycle")
        self.assertGreater(result["metrics"]["limited_samples"], 0)
        previous = None
        for r in result["rows"]:
            self.assertLessEqual(r["command_n"], 3+1e-12)
            self.assertTrue(all(math.isfinite(v) for v in r.values()))
            if previous and r["depth_m"] > 1e-12:
                self.assertLessEqual(math.hypot(r['fx_n']-previous['fx_n'],r['fy_n']-previous['fy_n']),50/c.rate+1e-12)
            previous = r

    def test_invalid_configuration_and_resource_bounds(self):
        for options in ({"tau":0},{"stiffness":float('inf')},{"rate":500.5},{"duration":1e9},{"depth":True}):
            with self.assertRaises(ValueError):
                ResearchConfig(**options)

    def test_same_trajectory_across_models(self):
        runs = [run_research(ResearchConfig(model=m)) for m in ("elastic","kelvin","sls")]
        for run in runs[1:]:
            self.assertEqual([r['depth_m'] for r in run['rows']],[r['depth_m'] for r in runs[0]['rows']])

    def test_immutable_export_and_deterministic_reproduction(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'run'
            write_research(str(out))
            data = json.loads((out/'session.json').read_text())
            self.assertEqual(data, run_research())
            with self.assertRaises(FileExistsError):
                write_research(str(out))

    def test_parameter_identification_and_heldout_prediction(self):
        def samples(ds, vs):
            return [{"depth_m":d,"velocity_m_s":v,"normal_n":720*d+9*max(0,v)} for d in ds for v in vs]
        fit = fit_kelvin(samples([.002,.004,.006],[.003,.013,.025]))
        self.assertAlmostEqual(fit['stiffness_n_m'],720)
        self.assertAlmostEqual(fit['damping_n_s_m'],9)
        evaluation = evaluate_fit(fit,samples([.003,.005],[.005,.017]))
        self.assertLess(evaluation['rmse_n'],1e-12)

    def test_identification_rejects_unidentifiable_design(self):
        with self.assertRaises(ValueError):
            fit_kelvin([{'depth_m':.003,'velocity_m_s':.01,'normal_n':2}]*5)
        with self.assertRaises(ValueError):
            evaluate_fit({'stiffness_n_m':2,'damping_n_s_m':1},[])


@unittest.skipUnless(shutil.which('node'), 'Node.js needed for independent browser parity')
class ResearchParityTests(unittest.TestCase):
    def node(self, script):
        return json.loads(subprocess.run(['node','-e',script],cwd=ROOT,check=True,capture_output=True,text=True).stdout)

    def test_all_sample_fields_match_across_models_and_protocols(self):
        rng = random.Random(949)
        for model in ('elastic','kelvin','sls'):
            for protocol in ('hold','cycle'):
                c = ResearchConfig(model=model, stiffness=rng.uniform(300,1500), tau=rng.uniform(.05,.6),
                    depth=rng.uniform(.002,.009),speed=rng.uniform(0,.09),rate=200)
                py = run_research(c,protocol)
                js = self.node("const m=require('./docs/assets/research-model.js');console.log(JSON.stringify(m.simulate("+json.dumps(py['config'])+","+json.dumps(protocol)+")));")
                self.assertEqual(len(py['rows']),len(js['rows']))
                for a,b in zip(py['rows'],js['rows']):
                    for k in a:
                        self.assertAlmostEqual(a[k],b[k],delta=1e-9,msg=f'{model}/{protocol}/{k}')

    def test_browser_import_recomputes_and_rejects_invalid_config(self):
        result = self.node("""
const m=require('./docs/assets/research-model.js');
const s=m.simulate();s.rows[0].command_n=999;
const restored=m.restore(JSON.stringify(s));let rejected=0;
for(const bad of [{...s,version:'9'}, {...s,config:{...s.config,rate:1e10}}, {...s,evidence:'human'}]){
 try{m.restore(JSON.stringify(bad));}catch(e){rejected++;}
}
console.log(JSON.stringify({command:restored.rows[0].command_n,rejected}));
""")
        self.assertEqual(result,{'command':0,'rejected':3})


if __name__ == '__main__':
    unittest.main()
