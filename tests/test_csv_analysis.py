import pytest

from preventia.csv_analysis import CSVValidationError, analyze_csv, profile_csv
from preventia.models import CSVAnalysisPlan


def test_profile_csv_is_deterministic_and_detects_formula_cells():
    content = "store,loss\n001,10.5\n002,=SUM(A1:A2)\n".encode()

    profile = profile_csv("losses.csv", content)

    assert profile.row_count == 2
    assert profile.columns == ["store", "loss"]
    assert profile.dataset_id.startswith("ds_")
    assert any("fórmula" in warning for warning in profile.warnings)


def test_profile_csv_rejects_non_csv():
    with pytest.raises(CSVValidationError):
        profile_csv("losses.xlsx", b"store,loss\n001,2")


def test_analyze_csv_uses_only_allowlisted_deterministic_operations():
    content = b"store,loss\n001,10\n001,5\n002,7\n"

    result = analyze_csv(
        "losses.csv",
        content,
        CSVAnalysisPlan(operation="sum", column="loss", group_by="store"),
    )

    assert result.value is None
    assert result.groups == {"001": 15.0, "002": 7.0}


def test_analyze_csv_rejects_unknown_operation_or_column():
    with pytest.raises(Exception):
        CSVAnalysisPlan(operation="exec", column="loss")
    with pytest.raises(CSVValidationError):
        analyze_csv(
            "losses.csv",
            b"store,loss\n001,10\n",
            CSVAnalysisPlan(operation="sum", column="missing"),
        )
