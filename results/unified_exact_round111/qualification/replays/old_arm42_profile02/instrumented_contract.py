def model_contract(root,p,path,arm):
    _t=time.perf_counter();m=lp_model(path);measure['model_read_parse']+=time.perf_counter()-_t
    _t=time.perf_counter();t=m['types'];names=m['order'];quantities=[n for n in names if n.startswith(('p_','d_'))]
    assert len(quantities)==2*p['V']*p['M']
    assert all(t[n]==('C' if arm=='M-B' else 'I') for n in quantities)
    assert all(t[n] in ['I','B'] for n in names if n.startswith(('x_','load_','Y_')))
    assert all(t[n]=='B' for n in names if n.startswith(('mode_','z_','state_')) and not n.startswith('state_g_'))
    modes=[n for n in names if n.startswith('mode_')];assert len(modes)==p['V']*p['M']
    measure['column_type_classification']+=time.perf_counter()-_t
    _t=time.perf_counter();counter=collections.Counter(m['rows']);measure['duplicate_row_Counter']+=time.perf_counter()-_t
    _t=time.perf_counter();a=evidence.instance(root,p);measure['input_read_parse']+=time.perf_counter()-_t;link_count=0
    if arm=='M-B':
        for i in range(1,p['V']+1):
            _t=time.perf_counter();terms={n:1. for n in quantities if n.endswith('_'+str(i))}
            selectors=[n for n in names if re.fullmatch(r'state_'+str(i)+r'_\d+',n)]
            measure['per_station_column_classification']+=time.perf_counter()-_t
            _t=time.perf_counter();assert selectors
            for n in selectors:
                amount=abs(a['b'][i]-int(n.rsplit('_',1)[1]))
                if amount:terms[n]=-float(amount)
            assert counter[(tuple(sorted(terms.items())),'=',0.)]>=1,('missing frozen A',path,i)
            terms={f'z_{k}_{i}':1. for k in range(p['M'])};selector=f'state_{i}_{a["b"][i]}'
            if selector in t:terms[selector]=1.
            assert counter[(tuple(sorted(terms.items())),'=',1.)]>=1,('missing frozen B',path,i)
            link_count+=2;measure['frozen_A_B_checks']+=time.perf_counter()-_t
    return dict(path=path.relative_to(root).as_posix(),SHA=sha(path),rows=len(m['rows']),columns=len(names),
        quantity_columns=len(quantities),quantity_type='C' if arm=='M-B' else 'I',direction_columns=len(modes),
        frozen_A_B_rows_checked=link_count,route_load_Y_integer=True,state_assignment_direction_binary=True),m
