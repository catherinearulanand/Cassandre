from decimal import Decimal

from cassandre_cc.calculations.covenant import Comparator, CovenantTest, evaluate_covenant
from cassandre_cc.domain.states import FindingState

_TEST = CovenantTest(
    test_id="T1",
    description="headroom ratio at least 5%",
    comparator=Comparator.AT_LEAST,
    threshold=Decimal("0.05"),
    near_threshold_band=Decimal("0.05"),  # +/- 5% of threshold = +/- 0.0025
)


def test_missing_value_is_indeterminate_not_compliant():
    assert evaluate_covenant(None, _TEST) is FindingState.INDETERMINATE


def test_comfortably_passing_value_is_compliant():
    assert evaluate_covenant(Decimal("0.20"), _TEST) is FindingState.COMPLIANT


def test_value_far_below_threshold_is_potential_breach():
    assert evaluate_covenant(Decimal("0.01"), _TEST) is FindingState.POTENTIAL_BREACH


def test_value_just_at_threshold_is_near_threshold_not_silently_compliant():
    assert evaluate_covenant(Decimal("0.05"), _TEST) is FindingState.NEAR_THRESHOLD
