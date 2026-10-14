"""
Test Suite: Multi-Ocean Teleconnection Intelligence
===================================================
Tests real data parsing, domain classification, coupled rainfall regime assessment,
and REST endpoints across Pacific, Indian, and Atlantic oceans.
"""
import pytest
from fastapi.testclient import TestClient

from agriminds.app import create_app
from agriminds.climate.sources.ocean_teleconnections import (
    classify_iod,
    classify_atlantic_gradient,
    compute_multi_ocean_coupled_risk,
    parse_psl_matrix_data,
    parse_oni_text,
    parse_oni_detailed,
    get_multi_ocean_engine,
)


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_classify_iod():
    pos = classify_iod(0.55)
    assert pos["phase"] == "Positive IOD"
    assert pos["risk_modifier"] == "FAVORABLE_MOISTURE"

    neg = classify_iod(-0.62)
    assert neg["phase"] == "Negative IOD"
    assert neg["risk_modifier"] == "ELEVATED_DROUGHT_RISK"

    neu = classify_iod(0.12)
    assert neu["phase"] == "Neutral IOD"


def test_classify_atlantic_gradient():
    # Warm North vs Cool South -> Northward pull
    pos_grad = classify_atlantic_gradient(tna=0.45, tsa=0.10)
    assert pos_grad["gradient"] == 0.35
    assert "Northward" in pos_grad["phase"]
    assert pos_grad["kiremt_outlook"] == "FAVORABLE_KIREMT_MONSOON"

    # Cool North vs Warm South -> Southward displacement
    neg_grad = classify_atlantic_gradient(tna=-0.20, tsa=0.30)
    assert neg_grad["gradient"] == -0.50
    assert "Southward" in neg_grad["phase"]
    assert neg_grad["kiremt_outlook"] == "DEFICIENT_MONSOON_RISK"


def test_compute_multi_ocean_coupled_risk():
    # El Nino + Neg Atlantic -> Severe Highland Kiremt risk
    risk = compute_multi_ocean_coupled_risk(nino34=1.2, dmi=0.1, atlantic_gradient=-0.35)
    assert risk["regime_a_highlands_risk"] >= 65.0
    assert risk["regime_a_status"] == "High Drought Risk"

    # La Nina + Neg IOD -> Severe Southern Lowlands (Regime C) risk
    risk_c = compute_multi_ocean_coupled_risk(nino34=-0.8, dmi=-0.55, atlantic_gradient=0.2)
    assert risk_c["regime_c_lowlands_risk"] >= 65.0
    assert risk_c["regime_c_status"] == "High Drought Risk"


def test_parse_psl_matrix():
    sample_text = """  1950  1950\n 1950    0.12   -0.23   -99.9   0.45   0.60   -0.10   0.00   0.15   -0.30   0.25   -0.40   0.50\n"""
    records = parse_psl_matrix_data(sample_text)
    assert len(records) == 11  # One missing (-99.9) filtered out
    assert records[0] == ("1950-01-01", 0.12)
    assert records[1] == ("1950-02-01", -0.23)


def test_parse_oni_text():
    sample_text = """ SEAS  YR   TOTAL   ANOM\n  DJF 2024  28.10   1.85\n  JFM 2024  28.20   1.62\n"""
    records = parse_oni_text(sample_text)
    assert len(records) == 2
    assert records[0] == ("2024-01-01", 1.85)
    assert records[1] == ("2024-02-01", 1.62)


def test_parse_oni_detailed_and_validation():
    # Test valid season parsing and NDJ year boundary centering
    text = (
        "SEAS  YR   TOTAL   ANOM\n"
        "DJF 2024  28.10   1.85\n"
        "NDJ 2024  27.40  -0.75\n"
    )
    detailed = parse_oni_detailed(text)
    assert len(detailed) == 2
    # DJF centered on Jan 01
    assert detailed[0]["date"] == "2024-01-01"
    assert detailed[0]["season"] == "DJF"
    assert detailed[0]["center_month"] == 1
    assert detailed[0]["oni_anom"] == 1.85
    assert detailed[0]["period_type"] == "3m_running_mean"
    # NDJ centered on Dec 01
    assert detailed[1]["date"] == "2024-12-01"
    assert detailed[1]["season"] == "NDJ"
    assert detailed[1]["center_month"] == 12
    assert detailed[1]["oni_anom"] == -0.75


def test_parse_oni_rejects_unknown_seasons_and_malformed():
    # Test that unknown season labels, non-numeric values, or corrupt rows are safely rejected
    corrupt_text = (
        "SEAS  YR   TOTAL   ANOM\n"
        "UNKNOWN 2024 28.10 1.85\n"     # Unknown season label (must NOT fallback to Jan)
        "XYZ 2024 28.10 1.85\n"         # Corrupt season
        "DJF NOT_YEAR 28.10 1.85\n"     # Non-numeric year
        "MAM 2024 NOT_FLOAT 1.85\n"     # Non-numeric SST
        "JJA 2024 28.10 NaN\n"           # NaN anomaly
        "SON 2024 28.10\n"               # Incomplete columns
        "DJF 2025 27.50 0.85\n"          # Valid row
    )
    detailed = parse_oni_detailed(corrupt_text)
    assert len(detailed) == 1
    assert detailed[0]["season"] == "DJF"
    assert detailed[0]["year"] == 2025
    assert detailed[0]["oni_anom"] == 0.85

    # Also test parse_oni_text
    simple = parse_oni_text(corrupt_text)
    assert len(simple) == 1
    assert simple[0] == ("2025-01-01", 0.85)


def test_api_ocean_endpoints(client):
    # Oceans Overview
    resp = client.get("/api/teleconnections/oceans")
    assert resp.status_code == 200
    data = resp.json()
    assert "pacific_ocean" in data
    assert "indian_ocean" in data
    assert "atlantic_ocean" in data
    assert "coupled_multi_ocean_assessment" in data

    # Indian Ocean
    resp_ind = client.get("/api/teleconnections/indian")
    assert resp_ind.status_code == 200
    assert resp_ind.json()["ocean"] == "Indian Ocean"

    # Atlantic Ocean
    resp_atl = client.get("/api/teleconnections/atlantic")
    assert resp_atl.status_code == 200
    assert resp_atl.json()["ocean"] == "Atlantic Ocean"

    # Coupled Regimes
    resp_reg = client.get("/api/teleconnections/coupled-regimes")
    assert resp_reg.status_code == 200
    assert "regime_a_highlands_risk" in resp_reg.json()
    assert "regime_c_lowlands_risk" in resp_reg.json()

    # Sync trigger
    resp_sync = client.post("/api/teleconnections/sync")
    assert resp_sync.status_code == 200
    assert resp_sync.json()["status"] == "ACCEPTED"
