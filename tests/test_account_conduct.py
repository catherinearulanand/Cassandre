from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
import pytest
from cassandre_cc.calculations.account_conduct import DailyConduct, evaluate_account_conduct

AS_OF = date(2026, 10, 1)

def rows(balance="50", credits="1", interest="0.5"):
    return [DailyConduct(AS_OF-timedelta(days=89-i), D(balance), D(credits), D(interest),
                         D("100"), D("80"), f"CBS:{i}") for i in range(90)]

def check(data, **kwargs):
    return evaluate_account_conduct(data, as_of=AS_OF, complete_day_end_feed=True, **kwargs)

def test_continuous_excess_uses_active_dp_and_resets():
    data = rows(balance="81")
    assert check(data).signals[0].status == "potential_trigger"
    data[0] = replace(data[0], outstanding_rupees=D("80"))
    assert check(data).consecutive_excess_days == 89
    assert check(data).signals[0].status == "not_triggered"

def test_no_credits_and_interest_are_independent():
    result = check(rows(credits="0", interest="0"))
    assert result.signals[1].status == "potential_trigger"
    assert result.signals[2].status == "not_triggered"

def test_interest_window_includes_asof_and_exact_coverage_is_not_trigger():
    data = rows(credits="1", interest="1")
    assert check(data).signals[2].status == "not_triggered"
    data[-1] = replace(data[-1], interest_debited_rupees=D("1.01"))
    result = check(data)
    assert result.signals[2].status == "potential_trigger"
    assert result.total_interest_rupees == D("90.01")
    assert result.window_start == AS_OF-timedelta(days=89)

@pytest.mark.parametrize("mutation", ["missing", "duplicate", "future", "nan", "negative", "float", "source"])
def test_bad_evidence_never_clears(mutation):
    data = rows()
    if mutation == "missing": data.pop(20)
    if mutation == "duplicate": data.append(data[0])
    if mutation == "future": data.append(replace(data[0], business_date=AS_OF+timedelta(days=1)))
    if mutation == "nan": data[0] = replace(data[0], credits_rupees=D("NaN"))
    if mutation == "negative": data[0] = replace(data[0], credits_rupees=D("-1"))
    if mutation == "float": data[0] = replace(data[0], credits_rupees=1.0)
    if mutation == "source": data[0] = replace(data[0], source_reference="")
    result = check(data)
    assert result.issues
    assert all(s.status == "indeterminate" for s in result.signals)

def test_unattested_and_nbfc_profile_never_clears():
    assert evaluate_account_conduct(rows(), as_of=AS_OF).issues
    assert check(rows(), profile="nbfc").issues

def test_equal_boundary_is_explicitly_unresolved():
    result = check(rows(balance="80", credits="0"))
    assert result.signals[1].status == "indeterminate"
    assert result.advisory_only

def test_changes_in_active_dp_apply_on_each_date():
    data = rows(balance="81")
    data[50] = replace(data[50], active_drawing_power_rupees=D("90"))
    assert check(data).consecutive_excess_days == 39
