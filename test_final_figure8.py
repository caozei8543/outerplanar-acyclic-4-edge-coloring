from outer4aec.figure8 import figure8_graph,figure8_labeled_edges
from outer4aec.core import validate_instance,verify_coloring
from outer4aec.certificates import validate_paper_certificates
import networkx as nx
import json
from pathlib import Path

def test_figure8_topology_and_stored_four_slot_certificate():
    g=figure8_graph();validate_instance(g)
    assert g.number_of_nodes()==71 and g.number_of_edges()==76
    assert nx.is_connected(g) and max(dict(g.degree()).values())==4
    assert g.number_of_edges()-g.number_of_nodes()+1==6
    f=Path(__file__).resolve().parents[1]/'data/certificates/figure8_transcribed_topology_and_validated_witness.json'
    data=json.loads(f.read_text())
    assert data['edges_1_based']==[list(e) for e in figure8_labeled_edges()]
    c={tuple(u-1 for u in entry['edge']):entry['slot'] for entry in data['verified_color_witness_1_based']}
    assert verify_coloring(g,c)[0]
