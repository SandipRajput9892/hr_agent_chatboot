import pytest

from app.tools.calculator import calculate_working_days
from app.tools.llm_tool import (
    LEAVE_BALANCES,
    get_employee_info,
    get_leave_balance,
    get_leave_requests,
    submit_leave_request,
)


# ---------------------------------------------------------------------------
# Calculator tests
# ---------------------------------------------------------------------------


def test_working_days_full_week():
    result = calculate_working_days("2026-04-27", "2026-05-01")
    assert result["working_days"] == 5


def test_working_days_spans_weekend():
    # Mon Apr 27 to Mon May 4 = 6 working days (Mon×2 + Tue–Fri)
    result = calculate_working_days("2026-04-27", "2026-05-04")
    assert result["working_days"] == 6


def test_working_days_single_day():
    result = calculate_working_days("2026-04-28", "2026-04-28")  # Tuesday
    assert result["working_days"] == 1


def test_working_days_invalid_range():
    result = calculate_working_days("2026-05-01", "2026-04-28")
    assert "error" in result


def test_working_days_bad_format():
    result = calculate_working_days("28-04-2026", "2026-05-01")
    assert "error" in result


# ---------------------------------------------------------------------------
# Employee info tests
# ---------------------------------------------------------------------------


def test_get_employee_found():
    result = get_employee_info("EMP001")
    assert result["found"] is True
    assert result["employee"]["name"] == "Rahul Sharma"


def test_get_employee_case_insensitive():
    result = get_employee_info("emp001")
    assert result["found"] is True


def test_get_employee_not_found():
    result = get_employee_info("EMP999")
    assert result["found"] is False


# ---------------------------------------------------------------------------
# Leave balance tests
# ---------------------------------------------------------------------------


def test_leave_balance_found():
    result = get_leave_balance("EMP001")
    assert result["found"] is True
    assert set(result["leave_balance"].keys()) == {"annual", "sick", "casual"}


def test_leave_balance_not_found():
    result = get_leave_balance("EMP999")
    assert result["found"] is False


# ---------------------------------------------------------------------------
# Leave request tests
# ---------------------------------------------------------------------------


def test_submit_leave_success():
    original = LEAVE_BALANCES["EMP002"]["annual"]
    result = submit_leave_request(
        employee_id="EMP002",
        leave_type="annual",
        start_date="2026-05-04",
        end_date="2026-05-05",
        reason="Personal work",
    )
    assert result["success"] is True
    assert result["days_requested"] == 2
    # restore
    LEAVE_BALANCES["EMP002"]["annual"] = original


def test_submit_leave_insufficient_balance():
    result = submit_leave_request(
        employee_id="EMP001",
        leave_type="annual",
        start_date="2026-05-04",
        end_date="2026-09-30",
        reason="Extended break",
    )
    assert result["success"] is False
    assert "Insufficient" in result["message"]


def test_submit_leave_invalid_type():
    result = submit_leave_request(
        employee_id="EMP001",
        leave_type="vacation",
        start_date="2026-05-04",
        end_date="2026-05-05",
        reason="Holiday",
    )
    assert result["success"] is False


def test_get_leave_requests_empty():
    result = get_leave_requests("EMP003")
    assert result["found"] is True
    assert result["total"] == 0
