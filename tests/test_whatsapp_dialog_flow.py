"""Regression test dialog WhatsApp TRAMOS.

Test ini menjaga flow percakapan tetap stabil tanpa perlu memanggil WhatsApp API.
Fokusnya adalah state machine: satu input menghasilkan satu transisi yang benar.
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.services.chatbot.conversation_coordinator import ConversationCoordinator
from app.services.chatbot.dialog_dispatcher import DialogFlowDispatcher
from app.services.chatbot.session_manager import ConversationSession, DialogState
from app.services.chatbot.smart_dialog_flow import SmartDialogFlowHandler


@pytest.fixture
def session():
    return ConversationSession("628123456789", "test-session")


@pytest.fixture
def stub_kb(monkeypatch):
    """Buat pencarian solusi selalu berhasil agar flow troubleshooting bisa diuji."""

    def fake_search(session, acknowledge_prefix=None):
        session.kb_solution = {"category": "gps", "confidence": 0.9}
        session.tried_kb_solution = True
        session.problem_category = "GPS"
        return (
            "Solusi GPS: restart perangkat dan cek sinyal.\n\n"
            "1️⃣ Ya, berhasil\n"
            "2️⃣ Tidak, masih error",
            DialogState.ASKING_SOLUTION_WORKED,
        )

    monkeypatch.setattr(
        SmartDialogFlowHandler,
        "_search_kb_smart",
        staticmethod(fake_search),
    )


def apply_turn(session, message):
    result = DialogFlowDispatcher.dispatch(session, message)
    session.current_state = result.next_state
    return result


def test_out_of_scope_does_not_enter_ticket_or_solution_flow(session):
    apply_turn(session, "halo")
    apply_turn(session, "caya")

    result = apply_turn(session, "presiden kocak")

    assert result.intent == "out_of_scope"
    assert session.current_state == DialogState.COLLECTING_PROBLEM
    assert session.problem_description is None
    assert "hanya dapat membantu" in result.response
    assert "Berhasil" not in result.response
    assert "buat tiket" not in result.response.lower()


def test_feedback_number_two_escalates_to_unit_collection(session, stub_kb):
    apply_turn(session, "halo")
    apply_turn(session, "caya")
    apply_turn(session, "gps tidak update di jalan")

    result = apply_turn(session, "2")

    assert result.intent == "solution_feedback"
    assert session.current_state == DialogState.COLLECTING_UNIT
    assert "unit atau kendaraan" in result.response.lower()


def test_menu_numbers_map_to_problem_and_search_solution(session, stub_kb):
    apply_turn(session, "halo")
    apply_turn(session, "caya")

    result = apply_turn(session, "2")

    assert result.intent == "troubleshooting"
    assert session.current_state == DialogState.ASKING_SOLUTION_WORKED
    assert session.problem_description == "Kamera atau dashcam mengalami error"
    assert "Solusi" in result.response


def test_ticket_data_collection_does_not_jump_back_to_feedback(session, stub_kb):
    apply_turn(session, "halo")
    apply_turn(session, "caya")
    apply_turn(session, "gps tidak update di jalan")
    apply_turn(session, "tidak, masih error")
    apply_turn(session, "B 1234 AB")
    apply_turn(session, "Tol Cikampek KM 42")
    result = apply_turn(session, "kemarin malam")

    assert session.current_state == DialogState.CONFIRMING_DETAILS
    assert session.vehicle_unit == "B 1234 AB"
    assert session.location == "Tol Cikampek KM 42"
    assert "malam" in session.issue_time
    assert "Ringkasan Tiket" in result.response


def test_required_unit_rejects_feedback_and_time_words(session):
    session.current_state = DialogState.COLLECTING_UNIT
    session.problem_description = "kamera error"
    session.problem_category = "Camera"

    # "tidak, masih error" = not a valid unit, stay at unit collection
    result = apply_turn(session, "tidak, masih error")
    assert session.current_state == DialogState.COLLECTING_UNIT
    assert session.vehicle_unit is None
    assert "wajib diisi" in result.response

    # "tadi pagi" = time keyword, not a valid unit. Unit remains mandatory.
    result = apply_turn(session, "tadi pagi")
    assert session.current_state == DialogState.COLLECTING_UNIT
    assert session.vehicle_unit is None
    assert "unit/kendaraan" in result.response


def test_required_location_rejects_time_words(session):
    session.current_state = DialogState.COLLECTING_LOCATION
    session.problem_description = "gps error"
    session.problem_category = "GPS"
    session.vehicle_unit = "B 1234 AB"

    result = apply_turn(session, "kemarin malam")

    assert session.current_state == DialogState.COLLECTING_LOCATION
    assert session.location is None
    assert "lokasi unit" in result.response


def test_information_request_answers_without_feedback_question(session, monkeypatch):
    session.current_state = DialogState.COLLECTING_PROBLEM

    monkeypatch.setattr(
        "app.services.chatbot.dialog_dispatcher.solution_searcher.search_solutions",
        lambda query, category=None: [{"category": "report", "confidence": 0.8}],
    )
    monkeypatch.setattr(
        "app.services.chatbot.dialog_dispatcher.solution_searcher.format_solution_for_user",
        lambda solution, user_context=None: "Panduan report: buka Dashboard > Reports.",
    )

    result = apply_turn(session, "bagaimana cara cek speeding report di dashboard")

    assert result.intent == "informational"
    assert session.current_state == DialogState.COLLECTING_PROBLEM
    assert "Panduan report" in result.response
    assert "Berhasil" not in result.response


def test_realtime_request_never_invents_live_location(session):
    session.current_state = DialogState.COLLECTING_PROBLEM

    apply_turn(session, "cek lokasi sekarang unit B 1234 AB")
    result = apply_turn(session, "B 1234 AB")

    assert result.intent == "realtime_request"
    assert session.current_state == DialogState.COLLECTING_PROBLEM
    assert "tidak akan mengarang" in result.response
    assert "Realtime Monitor" in result.response


def test_emergency_goes_directly_to_priority_ticket_collection(session):
    session.current_state = DialogState.COLLECTING_PROBLEM

    result = apply_turn(session, "truk kecelakaan dan ban pecah di tol")

    assert result.intent == "emergency"
    assert session.current_state == DialogState.COLLECTING_UNIT
    assert session.problem_category == "Emergency"
    assert session.problem_severity == "critical"
    assert "Utamakan keselamatan" in result.response


def test_correction_menu_updates_only_selected_field(session, stub_kb):
    apply_turn(session, "halo")
    apply_turn(session, "caya")
    apply_turn(session, "kamera error")
    apply_turn(session, "2")
    apply_turn(session, "Unit Lama")
    apply_turn(session, "Jakarta")
    apply_turn(session, "tadi pagi")
    apply_turn(session, "2")
    apply_turn(session, "2")
    result = apply_turn(session, "Unit Baru")

    assert session.current_state == DialogState.CONFIRMING_DETAILS
    assert session.vehicle_unit == "Unit Baru"
    assert session.location == "Jakarta"
    assert "Ringkasan Tiket" in result.response


def test_coordinator_local_dedup_and_lock(monkeypatch):
    monkeypatch.setattr(settings, "REDIS_URL", "")

    async def scenario():
        coordinator = ConversationCoordinator()
        assert await coordinator.claim_message("wamid.test") is True
        assert await coordinator.claim_message("wamid.test") is False

        async with coordinator.turn_lock("628123"):
            assert True

    asyncio.run(scenario())
