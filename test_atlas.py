from outer4aec.benchmarks import atlas_records
from outer4aec.core import q_graph
import networkx as nx

def test_final_atlas_predicate_is_332():
    records=atlas_records()
    assert len(records)==332
    assert sum(r['graph_id']=='atlas-G0840' for r in records)==1
    assert nx.is_isomorphic(q_graph(),nx.graph_atlas(840))
