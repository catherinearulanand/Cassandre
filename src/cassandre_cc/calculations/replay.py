"""Preserve an immutable derived-result receipt, without writing bank limits."""
import hashlib
import json
from dataclasses import asdict
from datetime import date, datetime
from enum import Enum

from cassandre_cc.domain.entities import CalculationRun
from cassandre_cc.store.memory_store import new_id


def _json(value):
    def encode(item):
        if isinstance(item, Enum):
            return item.value
        if isinstance(item, (date, datetime)):
            return item.isoformat()
        raise TypeError('Unsupported replay value')
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=encode, allow_nan=False)


def preserve_run(store, facility_id, result, actor):
    facility = store.facilities[facility_id]
    period = result.get('period')
    inputs = store.get_financials(facility_id, period) if period else None
    rule = store.effective_rule_version(facility_id, period) if period else None
    batches = tuple(sorted(key for key, item in store.financials_history.items()
                           if inputs is not None and item == inputs))
    inputs_json = _json(asdict(inputs) if inputs else None)
    rule_json = _json(asdict(rule) if rule else None)
    result_json = _json(result)
    digest = hashlib.sha256(_json({'inputs':inputs_json,'rule':rule_json,
                                 'result':result_json,'sources':batches}).encode()).hexdigest()
    run = CalculationRun(new_id('RUN'), facility.institution_id, facility_id, period,
                         actor, inputs_json, rule_json, result_json, batches, digest)
    store.calculation_runs[run.run_id] = run
    return run
