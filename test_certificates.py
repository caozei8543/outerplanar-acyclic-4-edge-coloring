import networkx as nx
from outer4aec.core import q_graph,exhaustive_4color,verify_coloring
from outer4aec.certificates import validate_paper_certificates
from outer4aec.dp import solve_graph

def test_paper_q_certificates():
    c=validate_paper_certificates()
    assert c['q_five_certificate_verified']
    assert c['q_is_isomorphic_to_networkx_G840']
    assert c['q_proper_four_colorings_up_to_permutation']==8
    assert len(c['table3_edge_deletion_certificates'])==11
    assert len(c['table4_six_vertex_certificates'])==2

def test_q_uncolorability_and_all_deletions():
    g=q_graph()
    assert exhaustive_4color(g) is None
    assert not solve_graph(g)['decision']['dominance']
    for e in g.edges():
        h=g.copy();h.remove_edge(*e)
        witness=exhaustive_4color(h)
        assert witness is not None
        assert verify_coloring(h,witness)[0]
        assert solve_graph(h)['decision']['dominance']
