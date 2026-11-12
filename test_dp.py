import random
import networkx as nx
from outer4aec.core import exhaustive_4color,verify_coloring
from outer4aec.benchmarks import zigzag_maximal,multiblock_chain,nonmaximal
from outer4aec.decomposition import build_block_tree,verify_tree,serialize_tree
from outer4aec.dp import solve_graph


def test_known_small_graphs():
    graphs=[nx.Graph(),nx.path_graph(5),nx.cycle_graph(8),zigzag_maximal(5),
            zigzag_maximal(6),zigzag_maximal(7),zigzag_maximal(12),
            multiblock_chain(24,random.Random(7)),nonmaximal(24,random.Random(19))]
    for g in graphs:
        r=solve_graph(g,include_trees=True)
        assert len(set(r['decision'].values()))==1
        # Restrict independent exhaustive oracle to at most 8 vertices.
        if len(g)<=8:
            expected=exhaustive_4color(g)
            assert r['decision']['dominance']==(expected is not None)
        for bl in r['blocks']:
            assert all(s['projection_equal'] and s['minimization_equal'] for s in bl['node_identities'])
        if r['decision']['dominance']:
            witness={tuple(v['edge']):v['color'] for v in r['certificates']['dominance']}
            assert verify_coloring(g,witness)[0]


def test_cycle_strict_dominance():
    r=solve_graph(nx.cycle_graph(8))
    assert r['metrics']['dominance']['cumulative_states']<r['metrics']['exposed']['cumulative_states']


def test_generator_stays_outerplanar():
    from outer4aec.core import validate_instance
    for n in (3,5,6,7,12,24,48,96,192):
        validate_instance(zigzag_maximal(n))
        if n>=12:
            validate_instance(nonmaximal(n,random.Random(n)))
            validate_instance(multiblock_chain(n,random.Random(n)))
