from dataclasses import replace
from datetime import date

from cassandre_cc.domain.states import ObligationState
from cassandre_cc.fixtures.synthetic_seed import seed
from cassandre_cc.store.memory_store import MemoryStore


def test_mid_month_amendment_is_unknown_for_monthly_input_but_exact_dates_replay():
    store = seed(MemoryStore())
    fid = 'SIM-FAC-B002'
    old = store.rule_versions_for_facility(fid)[0]
    new = replace(old, rule_set_id='SIM-MIDMONTH', version=2,
                  effective_from=date(2026, 9, 15), approved_by='checker.independent')
    store.rule_sets[new.rule_set_id] = new
    assert store.effective_rule_version(fid, '2026-09') is None
    assert store.effective_rule_on_date(fid, date(2026, 9, 14)) == old
    assert store.effective_rule_on_date(fid, date(2026, 9, 15)) == new
    assert store.effective_rule_version(fid, '2026-10') == new


def test_conflicting_effective_dates_fail_closed():
    store = seed(MemoryStore())
    old = store.rule_versions_for_facility('SIM-FAC-B002')[0]
    store.rule_sets['SIM-TIE'] = replace(old, rule_set_id='SIM-TIE', version=2)
    assert store.effective_rule_version(old.facility_id, '2026-07') is None


def test_retirement_does_not_destroy_historical_terms():
    store = seed(MemoryStore())
    old = store.rule_versions_for_facility('SIM-FAC-B002')[0]
    retired = replace(old, state=ObligationState.RETIRED)
    store.rule_sets[old.rule_set_id] = retired
    assert store.effective_rule_on_date(old.facility_id, old.effective_from) == retired


def test_invalid_period_does_not_select_terms():
    store = seed(MemoryStore())
    assert store.effective_rule_version('SIM-FAC-B002', '2026-99') is None
