from dataclasses import replace
import json

from cassandre_cc.calculations.replay import preserve_run
from cassandre_cc.fixtures.synthetic_seed import seed, INSTITUTION_ID
from cassandre_cc.store.memory_store import MemoryStore
from cassandre_cc.store import persistence


def test_run_retains_exact_inputs_after_replacement_and_roundtrips(tmp_path):
    store = seed(MemoryStore())
    fid = 'SIM-FAC-A001'
    original = store.get_financials(fid, '2026-07')
    store.financials_history['SIM-BATCH-ORIGINAL'] = original
    result = {'period':'2026-07','result_state':'calculated','proposed_dp':'4.165'}
    run = preserve_run(store, fid, result, 'maker.test')
    store.set_financials(replace(original, reported_stock_crore='9'))
    result['proposed_dp'] = '999'
    assert json.loads(run.inputs_json)['reported_stock_crore'] == original.reported_stock_crore
    assert json.loads(run.result_json)['proposed_dp'] == '4.165'
    assert run.source_batch_ids == ('SIM-BATCH-ORIGINAL',)
    path = tmp_path / 'snapshot.json'
    persistence.save(store, path)
    recovered = persistence.load(path)
    assert recovered.calculation_runs[run.run_id] == run
    assert recovered.financials_history['SIM-BATCH-ORIGINAL'] == original


def test_missing_inputs_preserved_as_unknown_not_zero():
    store = seed(MemoryStore())
    run = preserve_run(store, 'SIM-FAC-A001', {'period':'2020-01','result_state':'indeterminate'}, 'reader.test')
    assert json.loads(run.inputs_json) is None
    assert json.loads(run.rule_json) is None
    assert run.institution_id == INSTITUTION_ID
