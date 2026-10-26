"""Independent exact-dyadic oracle for the Round89 C++ pure fixture.

The fixture is produced by Round89NativeOtB1Micro pure-json PATH. This script
does not import the separator or call a solver; Fraction.from_float checks the
actual two-link binary64 coefficients and the submitted binary64 row.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path


def exact(value: float) -> Fraction:
    return Fraction.from_float(float(value))


def audit(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    alpha = [exact(v) for v in data["alpha"]]
    gamma = [[exact(v) for v in station] for station in data["gamma"]]
    beta = [[exact(v) for v in station] for station in data["beta"]]
    state_errors = [[exact(v) for v in station]
                    for station in data["state_support_errors"]]
    actual_support = [[alpha[i] * gamma[i][y] for y in range(3)]
                      for i in range(2)]
    for i in range(2):
        for y in range(3):
            assert abs(beta[i][y] - actual_support[i][y]) <= state_errors[i][y]
    assert (max(state_errors[0]) + max(state_errors[1])
            <= exact(data["support_error"]))
    nonexact_products = 0
    for station in range(2):
        for item in data["wide_nonexact_products"][station]:
            true_value = alpha[station] * exact(item["gamma"])
            difference = abs(exact(item["beta"]) - true_value)
            assert difference <= exact(item["error"])
            nonexact_products += difference > 0
    assert nonexact_products > 0, "gamma 3/5 must exercise rounded product"

    knots = sorted(set(beta[0] + beta[1]))
    def check_cut(payload: dict, masses: list[list[Fraction]]) -> list[int]:
        signs: list[int] = []
        for threshold in knots[:-1]:
            cdf_i = sum(masses[0][y] for y in range(3)
                        if beta[0][y] <= threshold)
            cdf_j = sum(masses[1][y] for y in range(3)
                        if beta[1][y] <= threshold)
            signs.append(1 if cdf_i - cdf_j >= 0 else -1)

        def exact_suffix(value: Fraction) -> Fraction:
            return sum((Fraction(signs[k]) * (knots[k + 1] - knots[k])
                        for k in range(len(signs)) if value <= knots[k]),
                       Fraction(0))

        ideal = [{6 + y: -exact_suffix(beta[0][y]) for y in range(3)},
                 {9 + y: exact_suffix(beta[1][y]) for y in range(3)}]
        submitted = dict(zip(payload["indices"],
                             (exact(v) for v in payload["coefficients"])))
        assert submitted[5] == 1
        error_by_station = [
            max(abs(submitted[index] - coefficient)
                for index, coefficient in station.items())
            for station in ideal
        ]
        assert sum(error_by_station) <= exact(payload["coefficient_error"])
        rhs = exact(payload["rhs"])
        for y in range(3):
            for z in range(3):
                h = abs(actual_support[0][y] - actual_support[1][z])
                lhs = h + submitted[6 + y] + submitted[9 + z]
                assert lhs >= rhs, (y, z, lhs, rhs)
        assert payload["status"] == "reliably_violated"
        return signs

    signs = check_cut(
        data["cut"],
        [[Fraction(1, 2), Fraction(0), Fraction(1, 2)],
         [Fraction(0), Fraction(1), Fraction(0)]])
    reverse_signs = check_cut(
        data["reverse_cut"],
        [[Fraction(0), Fraction(1), Fraction(0)],
         [Fraction(1, 2), Fraction(0), Fraction(1, 2)]])
    assert 1 in signs and -1 in signs
    assert 1 in reverse_signs and -1 in reverse_signs
    assert signs != reverse_signs
    wide_beta = [[exact(v) for v in station]
                 for station in data["wide_beta"]]
    wide_actual = [[alpha[i] * Fraction(y) for y in range(6)]
                   for i in range(2)]
    wide_support_error = exact(data["wide_support_error"])
    assert (max(abs(wide_beta[0][y] - wide_actual[0][y])
                for y in range(6)) +
            max(abs(wide_beta[1][y] - wide_actual[1][y])
                for y in range(6)) <= wide_support_error)
    wide_knots = sorted(set(wide_beta[0] + wide_beta[1]))
    wide_masses = [[Fraction(1, 2), Fraction(0), Fraction(1, 2),
                    Fraction(0), Fraction(0), Fraction(0)],
                   [Fraction(0), Fraction(1), Fraction(0),
                    Fraction(0), Fraction(0), Fraction(0)]]
    wide_signs = []
    for threshold in wide_knots[:-1]:
        first = sum(wide_masses[0][y] for y in range(6)
                    if wide_beta[0][y] <= threshold)
        second = sum(wide_masses[1][y] for y in range(6)
                     if wide_beta[1][y] <= threshold)
        wide_signs.append(1 if first - second >= 0 else -1)
    assert 1 in wide_signs and -1 in wide_signs

    def wide_suffix(value: Fraction) -> Fraction:
        return sum((Fraction(wide_signs[k]) *
                    (wide_knots[k + 1] - wide_knots[k])
                    for k in range(len(wide_signs))
                    if value <= wide_knots[k]), Fraction(0))

    wide_payload = data["wide_cut"]
    wide_submitted = dict(zip(wide_payload["indices"],
                              (exact(v) for v in
                               wide_payload["coefficients"])))
    assert len(wide_submitted) == 13 and wide_submitted[5] == 1
    wide_ideal = [{6 + y: -wide_suffix(wide_beta[0][y])
                   for y in range(6)},
                  {12 + y: wide_suffix(wide_beta[1][y])
                   for y in range(6)}]
    wide_coeff_error = sum((max(abs(wide_submitted[col] - value)
                                for col, value in station.items())
                            for station in wide_ideal), Fraction(0))
    assert wide_coeff_error <= exact(wide_payload["coefficient_error"])
    wide_rhs = exact(wide_payload["rhs"])
    assert wide_rhs <= -(wide_support_error +
                         exact(wide_payload["coefficient_error"]))
    for y in range(6):
        for z in range(6):
            minimum_h = abs(wide_actual[0][y] - wide_actual[1][z])
            lhs = (minimum_h + wide_submitted[6 + y] +
                   wide_submitted[12 + z])
            assert lhs >= wide_rhs, ("rounded_product_row", y, z, lhs,
                                      wide_rhs)
    assert wide_payload["status"] == "reliably_violated"
    return {"checked_integer_points": 54,
            "exact_two_link_chain": True,
            "nonexact_gamma_products": nonexact_products,
            "both_sign_orientations": True,
            "rounded_product_cut_all_36_points": True,
            "support_envelopes": True,
            "coefficient_envelope": True,
            "submitted_row_valid": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-json", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(args.fixture_json)
        result["status"] = "passed"
        code = 0
    except Exception as exc:
        result = {"status": "failed", "reason": repr(exc)}
        code = 1
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True),
                            encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
