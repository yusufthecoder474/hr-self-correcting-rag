import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[2]/'research/review3/finalization/benchmark.py'
spec=importlib.util.spec_from_file_location('benchmark',P);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class Policy:
    def predict(self,**kwargs):return 'STOP',.9
class Backend:
    TOP_K=3;_halting_policy=Policy()
    def __init__(self):self.calls=0
    def retrieve_chunks(self,q,k):self.calls+=1;return ['evidence'],[.2],[]
    def build_candidates(self,q,c,d):return [(1,c[0])]
    def select_final_context(self,q,c):return c[0][1]
    def evaluate_retrieval(self,q,c):return .4,'INSUFFICIENT'
    def rewrite_query(self,q):return q
@pytest.mark.parametrize('policy,expected',[('single',1),('learned',1),('critic',1),('budget',3)])
def test_budget_is_actual_retrieval_count(policy,expected):
    backend=Backend();_,t=b.loop('q',backend,policy)
    assert backend.calls==expected==len(t)
    assert t[-1]['critic_decision']=='INSUFFICIENT'
    if policy=='budget':assert t[-1]['stop_reason']=='budget_exhausted'
def test_feature_delta_is_prior_best():
    class Rewriting(Backend):
        def rewrite_query(self,q):return q+'x'
        def evaluate_retrieval(self,q,c):return [.6,.4,.7][self.calls-1],'INSUFFICIENT'
    _,t=b.loop('q',Rewriting(),'budget')
    assert t[1]['score_delta']==pytest.approx(-.2)
    assert t[2]['score_delta']==pytest.approx(.1)
def test_final_benchmark_rejects_unapproved_dataset(tmp_path):
    with pytest.raises((FileNotFoundError,ValueError,ModuleNotFoundError)):
        b.run('frozen',tmp_path/'run',1)
def test_unknown_policy_rejected():
    with pytest.raises(ValueError):b.loop('q',Backend(),'fake')
