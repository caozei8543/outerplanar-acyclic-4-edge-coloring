from outer4aec.states import formal_enumeration,eligible_mask,State,minimize,project,leaf

def test_paper_tables_1_and_2():
    r=formal_enumeration()
    assert r['full_formal_states']==16384
    assert r['exposed_formal_states']==956
    assert r['antichain_upper_bound']==468
    assert r['orbit_count']==82
    assert r['table_1']=={'0':60,'1':48,'2':120,'3':16,'4':12}
    assert r['fixed_counts_by_cycle_type_totals']=={'1,1,1,1':956,'2,1,1':744,'2,2':84,'3,1':160,'4':24}

def test_pair_eligibility_and_dominance():
    # A=B={1,2}, exposed pairs contain one of {1,2} and one of {3,4}
    mask=eligible_mask(3,3)
    assert mask.bit_count()==4
    assert eligible_mask(0,15)==0
    q={State(3,3,0),State(3,3,1),State(3,3,3),State(1,2,0)}
    assert minimize(q)=={State(3,3,0),State(1,2,0)}
    assert project(leaf(1))==leaf(1)
