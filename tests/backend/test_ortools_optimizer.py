"""
Stage 6 Unit & Integration Tests: Google OR-Tools CP-SAT Recovery Optimization Engine.
Tests multiple scenarios including the prompt's Train A / B / C example, connection buffers,
objective weight sensitivity, seat availability, passenger preferences, and infeasibility.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.optimization_schemas import (
    OptimizationRequest,
    OptimizationConstraints,
    TravelerPreferences,
    OptimizationWeights,
    CandidateAlternativeInput
)
from app.modules.optimization.ortools_optimizer import ortools_recovery_optimizer

client = TestClient(app)


def _get_prompt_trains():
    return [
        CandidateAlternativeInput(
            transport_id="TRAIN-A",
            name="Train A",
            supplier_type="train",
            provider="Indian Railways",
            origin="Delhi",
            destination="Jaipur",
            departure="5:00 PM",
            arrival="8:30 PM",
            price=500.0,
            currency="INR",
            available_seats=10,
            number_of_changes=0,
            reliability=0.95
        ),
        CandidateAlternativeInput(
            transport_id="TRAIN-B",
            name="Train B",
            supplier_type="train",
            provider="Indian Railways",
            origin="Delhi",
            destination="Jaipur",
            departure="5:30 PM",
            arrival="9:00 PM",
            price=700.0,
            currency="INR",
            available_seats=10,
            number_of_changes=0,
            reliability=0.95
        ),
        CandidateAlternativeInput(
            transport_id="TRAIN-C",
            name="Train C",
            supplier_type="train",
            provider="Indian Railways",
            origin="Delhi",
            destination="Jaipur",
            departure="7:00 PM",
            arrival="10:30 PM",
            price=400.0,
            currency="INR",
            available_seats=10,
            number_of_changes=0,
            reliability=0.90
        )
    ]


def test_scenario_1_prompt_example_hotel_checkin_cutoff():
    """
    Scenario 1 (Prompt Example):
    Train A (5:00 PM, ₹500, Arr 8:30 PM)
    Train B (5:30 PM, ₹700, Arr 9:00 PM)
    Train C (7:00 PM, ₹400, Arr 10:30 PM)
    Hotel latest check-in: 10:00 PM
    Train C must be rejected despite being cheapest (₹400), and Train A selected over Train B.
    """
    req = OptimizationRequest(
        available_alternatives=_get_prompt_trains(),
        constraints=OptimizationConstraints(
            current_arrival="4:00 PM",
            hotel_latest_checkin="10:00 PM",
            min_connection_minutes=30,
            required_seats=1
        ),
        traveler_preferences=TravelerPreferences()
    )
    res = ortools_recovery_optimizer.optimize(req)

    assert res.constraints_satisfied is True
    assert res.selected_option is not None
    assert res.selected_option["transport_id"] == "TRAIN-A"
    assert res.solver_metadata["solver"] == "Google OR-Tools CP-SAT"
    assert res.solver_metadata["status"] == "OPTIMAL"

    # Verify Train C was marked infeasible due to hotel latest check-in constraint
    train_c = next(a for a in res.alternatives if a["transport_id"] == "TRAIN-C")
    assert train_c["feasible"] is False
    assert train_c["constraint_checks"]["arrival_before_hotel_checkin"] is False


def test_scenario_2_connection_time_buffer_prunes_train_a():
    """
    Scenario 2:
    Traveler arrives at 4:30 PM and requires at least 45 minutes connection buffer (earliest departure 5:15 PM).
    Train A (5:00 PM) violates connection_time_feasible; Train C (10:30 PM) violates hotel check-in;
    OR-Tools selects Train B (5:30 PM, arrives 9:00 PM).
    """
    req = OptimizationRequest(
        available_alternatives=_get_prompt_trains(),
        constraints=OptimizationConstraints(
            current_arrival="4:30 PM",
            hotel_latest_checkin="10:00 PM",
            min_connection_minutes=45,
            required_seats=1
        )
    )
    res = ortools_recovery_optimizer.optimize(req)

    assert res.constraints_satisfied is True
    assert res.selected_option is not None
    assert res.selected_option["transport_id"] == "TRAIN-B"

    train_a = next(a for a in res.alternatives if a["transport_id"] == "TRAIN-A")
    assert train_a["feasible"] is False
    assert train_a["constraint_checks"]["connection_time_feasible"] is False


def test_scenario_3_configurable_weights_price_vs_speed():
    """
    Scenario 3:
    Verify configurable objective weights shift the OR-Tools optimal solution
    between a low-cost train and a fast expensive flight.
    """
    options = [
        CandidateAlternativeInput(
            transport_id="FLT-FAST",
            name="Express Flight",
            supplier_type="flight",
            provider="IndiGo",
            departure="17:30",
            arrival="18:30",
            price=3850.0,
            available_seats=6,
            number_of_changes=0,
            reliability=0.96
        ),
        CandidateAlternativeInput(
            transport_id="TRN-ECON",
            name="Economy Train",
            supplier_type="train",
            provider="IRCTC",
            departure="17:30",
            arrival="22:00",
            price=800.0,
            available_seats=15,
            number_of_changes=1,
            reliability=0.88
        )
    ]

    # Case A: Budget-conscious traveler (high weight on price)
    budget_req = OptimizationRequest(
        available_alternatives=options,
        constraints=OptimizationConstraints(current_arrival="16:00", hotel_latest_checkin="23:00", min_connection_minutes=45),
        traveler_preferences=TravelerPreferences(
            weights=OptimizationWeights(
                price=0.85,
                travel_time=0.05,
                waiting_time=0.05,
                number_of_changes=0.0,
                arrival_time=0.05,
                reliability=0.0
            )
        )
    )
    budget_res = ortools_recovery_optimizer.optimize(budget_req)
    assert budget_res.selected_option["transport_id"] == "TRN-ECON"

    # Case B: Time-critical traveler (high weight on travel_time, arrival_time, reliability, changes)
    speed_req = OptimizationRequest(
        available_alternatives=options,
        constraints=OptimizationConstraints(current_arrival="16:00", hotel_latest_checkin="23:00", min_connection_minutes=45),
        traveler_preferences=TravelerPreferences(
            weights=OptimizationWeights(
                price=0.05,
                travel_time=0.45,
                waiting_time=0.05,
                number_of_changes=0.15,
                arrival_time=0.20,
                reliability=0.10
            )
        )
    )
    speed_res = ortools_recovery_optimizer.optimize(speed_req)
    assert speed_res.selected_option["transport_id"] == "FLT-FAST"


def test_scenario_4_availability_and_passenger_preferences():
    """
    Scenario 4:
    Verify seat availability, mode exclusion, and max_changes constraints are enforced by CP-SAT.
    """
    options = [
        CandidateAlternativeInput(
            transport_id="OPT-LOW-SEATS",
            name="Almost Full Train",
            supplier_type="train",
            departure="17:00",
            arrival="20:00",
            price=500.0,
            available_seats=1,  # Fails required_seats=3
            number_of_changes=0
        ),
        CandidateAlternativeInput(
            transport_id="OPT-BUS-EXCLUDED",
            name="Sleeper Bus",
            supplier_type="bus",  # Excluded by passenger preference
            departure="17:00",
            arrival="21:00",
            price=450.0,
            available_seats=10,
            number_of_changes=0
        ),
        CandidateAlternativeInput(
            transport_id="OPT-VALID-TRAIN",
            name="Valid Direct Train",
            supplier_type="train",
            departure="17:30",
            arrival="21:00",
            price=750.0,
            available_seats=8,
            number_of_changes=0
        )
    ]

    req = OptimizationRequest(
        available_alternatives=options,
        constraints=OptimizationConstraints(
            current_arrival="16:00",
            hotel_latest_checkin="22:00",
            min_connection_minutes=30,
            required_seats=3
        ),
        traveler_preferences=TravelerPreferences(
            excluded_modes=["bus"],
            max_changes=0
        )
    )
    res = ortools_recovery_optimizer.optimize(req)
    assert res.constraints_satisfied is True
    assert res.selected_option["transport_id"] == "OPT-VALID-TRAIN"


def test_scenario_5_infeasible_constraints():
    """
    Scenario 5:
    When current_arrival is after all departures, OR-Tools reports INFEASIBLE and constraints_satisfied=False.
    """
    req = OptimizationRequest(
        available_alternatives=_get_prompt_trains(),
        constraints=OptimizationConstraints(
            current_arrival="8:00 PM",  # After all train departures (5:00 PM, 5:30 PM, 7:00 PM)
            hotel_latest_checkin="10:00 PM",
            min_connection_minutes=30
        )
    )
    res = ortools_recovery_optimizer.optimize(req)
    assert res.constraints_satisfied is False
    assert res.selected_option is None
    assert res.solver_metadata["status"] == "INFEASIBLE"


def test_scenario_6_api_endpoint_and_mock_supplier_integration():
    """
    Scenario 6:
    Verify POST /api/v1/recovery/optimize with auto_fetch_from_suppliers=True fetches
    live alternatives from Stage 5 Mock Suppliers and optimizes with OR-Tools.
    """
    response = client.post(
        "/api/v1/recovery/optimize",
        json={
            "origin": "Delhi",
            "destination": "Jaipur",
            "auto_fetch_from_suppliers": True,
            "constraints": {
                "current_arrival": "2026-10-20T16:00:00",
                "hotel_latest_checkin": "2026-10-20T23:00:00",
                "min_connection_minutes": 60,
                "required_seats": 1
            },
            "traveler_preferences": {
                "max_budget": 5000.0,
                "allowed_modes": ["flight", "train", "bus"],
                "excluded_modes": []
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["constraints_satisfied"] is True
    assert data["selected_option"] is not None
    assert len(data["alternatives"]) >= 5
    assert "Google OR-Tools CP-SAT" in data["explanation"]
