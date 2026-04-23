"""
End-to-end Database Integration Test
=====================================
Simulates a complete WhatsApp conversation flow and verifies
that ALL 13 database tables are populated correctly.

Tests:
1. Full flow: greeting → name → problem → KB solution → feedback → unit → location → time → confirm → ticket
2. Verifies every table has correct data
3. Tests server-restart resilience (get_or_create_conversation)
4. Tests CLOSED → new conversation flow
"""

import sys
import os
import time

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.database_tracker import db_tracker, init_db_tracker
from app.database_models import (
    DatabaseManager, User, Conversation, MessageHistory, Ticket, Resolution,
    AnalyticsData, ConversationContext, ConversationTurn,
    UserProfileData, SolutionAttempt, SolutionEffectiveness,
    WhatsAppSession, ConversationState,
)
from sqlalchemy import text

# Test phone number (unique to avoid conflicts)
TEST_PHONE = f"TEST_{int(time.time())}"
TEST_NAME = "Test Driver"

print("=" * 60)
print("DATABASE INTEGRATION TEST")
print("=" * 60)

# ============================================================================
# STEP 1: Initialize
# ============================================================================
print("\n[1/8] Initializing database tracker...")
init_db_tracker()
assert db_tracker.db_manager is not None, "DatabaseTracker not initialized!"
print("  ✅ DatabaseTracker initialized")

# ============================================================================
# STEP 2: Create user
# ============================================================================
print("\n[2/8] Testing user creation...")
user_id = db_tracker.get_or_create_user(TEST_PHONE, TEST_NAME)
assert user_id is not None, "Failed to create user!"
print(f"  ✅ User created: id={user_id}")

# Verify idempotency
user_id_2 = db_tracker.get_or_create_user(TEST_PHONE, TEST_NAME)
assert user_id == user_id_2, f"get_or_create_user not idempotent! {user_id} != {user_id_2}"
print(f"  ✅ User idempotent: same id={user_id_2}")

# ============================================================================
# STEP 3: Test get_or_create_conversation (CRITICAL FIX)
# ============================================================================
print("\n[3/8] Testing conversation creation + resilience...")
conv_id = db_tracker.get_or_create_conversation(TEST_PHONE, user_id)
assert conv_id is not None, "Failed to create conversation!"
print(f"  ✅ Conversation created: id={conv_id}")

# Simulate server restart — call again, should find existing conversation
conv_id_2 = db_tracker.get_or_create_conversation(TEST_PHONE, user_id)
assert conv_id == conv_id_2, f"Duplicate conversation created! {conv_id} != {conv_id_2}"
print(f"  ✅ Server-restart resilience: reused id={conv_id_2} (no duplicate)")

# ============================================================================
# STEP 4: Simulate full conversation flow with tracking
# ============================================================================
print("\n[4/8] Simulating full conversation flow...")

# Turn 1: GREETING
db_tracker.track_full_turn(
    TEST_PHONE, "halo", 
    "Selamat datang di TRAMOS! Siapa nama Anda?",
    conv_id, turn_number=1, current_state="collecting_name",
    intent="greeting", processing_time_ms=50
)
print("  ✅ Turn 1: GREETING tracked")

# Turn 2: COLLECTING_NAME
db_tracker.track_full_turn(
    TEST_PHONE, TEST_NAME,
    f"Terima kasih {TEST_NAME}! Apa masalah Anda?",
    conv_id, turn_number=2, current_state="collecting_problem",
    intent="data_collection", processing_time_ms=30
)
db_tracker.update_user_name(TEST_PHONE, TEST_NAME)
print("  ✅ Turn 2: NAME collected, user updated")

# Turn 3: COLLECTING_PROBLEM + KB search
db_tracker.track_full_turn(
    TEST_PHONE, "GPS tidak akurat",
    "Coba langkah ini: 1. Restart GPS...\n\nApakah solusi ini membantu?",
    conv_id, turn_number=3, current_state="asking_solution_worked",
    intent="solution_search", category="GPS", processing_time_ms=120
)
db_tracker.update_conversation_state(conv_id, "asking_solution_worked",
    category="GPS", issue_description="GPS tidak akurat")
# Log solution attempt
attempt_id = db_tracker.log_solution_attempt(
    conversation_id=conv_id, phone_number=TEST_PHONE,
    solution_id="gps", category="GPS",
    problem_description="GPS tidak akurat",
    kb_match_score=0.85
)
assert attempt_id is not None, "Failed to create solution attempt!"
print(f"  ✅ Turn 3: PROBLEM tracked, solution attempt={attempt_id}")

# Test get_active_solution_attempt (CRITICAL FIX)
recovered_attempt = db_tracker.get_active_solution_attempt(conv_id)
assert recovered_attempt == attempt_id, f"Failed to recover attempt! got {recovered_attempt}, expected {attempt_id}"
print(f"  ✅ Solution attempt recovery works: {recovered_attempt}")

# Turn 4: ASKING_SOLUTION_WORKED → escalate (user says "tidak")
db_tracker.track_full_turn(
    TEST_PHONE, "tidak berhasil",
    "Baik, mari kita buat tiket. Nomor unit kendaraan?",
    conv_id, turn_number=4, current_state="collecting_unit",
    intent="solution_feedback", category="GPS", processing_time_ms=25
)
db_tracker.update_solution_outcome(attempt_id, "escalated", escalation_needed=True)
print("  ✅ Turn 4: SOLUTION_FEEDBACK tracked, outcome=escalated")

# Turn 5: COLLECTING_UNIT
db_tracker.track_full_turn(
    TEST_PHONE, "B 1234 XY",
    "Di mana lokasi Anda saat ini?",
    conv_id, turn_number=5, current_state="collecting_location",
    intent="data_collection", category="GPS", processing_time_ms=20
)
print("  ✅ Turn 5: UNIT collected")

# Turn 6: COLLECTING_LOCATION
db_tracker.track_full_turn(
    TEST_PHONE, "Jakarta Selatan",
    "Kapan masalah ini terjadi?",
    conv_id, turn_number=6, current_state="collecting_time",
    intent="data_collection", category="GPS", processing_time_ms=20
)
print("  ✅ Turn 6: LOCATION collected")

# Turn 7: COLLECTING_TIME
db_tracker.track_full_turn(
    TEST_PHONE, "tadi pagi",
    "Konfirmasi data:\n- Nama: Test Driver\n- Masalah: GPS\nSudah benar?",
    conv_id, turn_number=7, current_state="confirming_details",
    intent="data_collection", category="GPS", processing_time_ms=20
)
print("  ✅ Turn 7: TIME collected")

# Turn 8: CONFIRMING_DETAILS → create ticket
db_tracker.track_full_turn(
    TEST_PHONE, "ya",
    "Tiket berhasil dibuat! #12345",
    conv_id, turn_number=8, current_state="closed",
    intent="confirmation", category="GPS", processing_time_ms=500
)
print("  ✅ Turn 8: CONFIRMATION tracked")

# Ticket creation tracking
ticket_id = db_tracker.create_ticket_record(
    user_id=user_id, phone_number=TEST_PHONE,
    conversation_id=conv_id, osticket_id=12345,
    subject="[GPS] Issue Report - Test Driver",
    description="GPS tidak akurat, unit B 1234 XY, Jakarta Selatan",
    category="GPS", priority="medium"
)
assert ticket_id is not None, "Failed to create ticket record!"
print(f"  ✅ Ticket record created: id={ticket_id}")

# Resolution
db_tracker.create_resolution(
    ticket_id=ticket_id, resolution_type="escalated",
    resolution_notes="Escalated via WhatsApp. KB solution tried.",
    ai_attempted=True, ai_successful=False, resolution_time_minutes=5
)
print("  ✅ Resolution created")

# User profile + analytics
db_tracker.increment_user_tickets(TEST_PHONE)
db_tracker.update_user_profile(TEST_PHONE, "GPS", issue_resolved=False)
db_tracker.log_analytics("ticket_volume", 1.0, "GPS", conversation_id=conv_id, ticket_id=ticket_id)
db_tracker.update_conversation_state(conv_id, "closed", category="GPS", intent="ticket_created")
print("  ✅ Profile, analytics, conversation state updated")

# Dashboard
db_tracker.update_dashboard_summary()
print("  ✅ Dashboard summary updated")

# ============================================================================
# STEP 5: Test close_conversation (NEW)
# ============================================================================
print("\n[5/8] Testing close_conversation...")
db_tracker.close_conversation(conv_id, "closed")
# New conversation should be created since old one is closed
conv_id_3 = db_tracker.get_or_create_conversation(TEST_PHONE, user_id)
assert conv_id_3 != conv_id, f"Should create new conversation after close! got {conv_id_3}"
print(f"  ✅ After close: new conversation id={conv_id_3} (old was {conv_id})")

# Close the new one too for cleanup
db_tracker.close_conversation(conv_id_3, "closed")

# ============================================================================
# STEP 6: Verify ALL 13 tables have data
# ============================================================================
print("\n[6/8] Verifying all 13 tables have data...")

db = db_tracker._get_db()
tables_check = {
    "users": db.query(User).filter_by(phone_number=TEST_PHONE).count(),
    "conversations": db.query(Conversation).filter_by(phone_number=TEST_PHONE).count(),
    "message_history": db.query(MessageHistory).filter_by(phone_number=TEST_PHONE).count(),
    "conversation_turns": db.query(ConversationTurn).filter_by(phone_number=TEST_PHONE).count(),
    "conversation_context": db.query(ConversationContext).filter_by(phone_number=TEST_PHONE).count(),
    "tickets": db.query(Ticket).filter_by(phone_number=TEST_PHONE).count(),
    "resolutions": db.execute(text(
        f"SELECT COUNT(*) FROM resolutions r JOIN tickets t ON r.ticket_id=t.id WHERE t.phone_number='{TEST_PHONE}'"
    )).scalar(),
    "analytics_data": db.query(AnalyticsData).filter_by(conversation_id=conv_id).count(),
    "user_profile_data": db.query(UserProfileData).filter_by(phone_number=TEST_PHONE).count(),
    "solution_attempts": db.query(SolutionAttempt).filter_by(phone_number=TEST_PHONE).count(),
    "solution_effectiveness": db.execute(text(
        "SELECT COUNT(*) FROM solution_effectiveness WHERE solution_id='gps' AND category='GPS'"
    )).scalar(),
    "dashboard_analytics_summary": db.execute(text(
        "SELECT COUNT(*) FROM dashboard_analytics_summary"
    )).scalar(),
}

# whatsapp_sessions not managed by db_tracker (managed by session_manager)
# but check it exists
ws_count = db.query(WhatsAppSession).count()
tables_check["whatsapp_sessions"] = ws_count

all_ok = True
for table, count in tables_check.items():
    status = "✅" if count > 0 else "❌ EMPTY"
    if count == 0:
        all_ok = False
    print(f"  {status} {table:35s} {count} rows")

# Expected minimums
expected = {
    "users": 1,
    "conversations": 2,  # original + new after close
    "message_history": 16,  # 8 turns × 2 messages each
    "conversation_turns": 8,
    "conversation_context": 1,
    "tickets": 1,
    "resolutions": 1,
    "analytics_data": 1,
    "user_profile_data": 1,
    "solution_attempts": 1,
    "solution_effectiveness": 1,
    "dashboard_analytics_summary": 1,
}

print("\n[7/8] Verifying data counts...")
for table, min_count in expected.items():
    actual = tables_check[table]
    if actual < min_count:
        print(f"  ❌ {table}: expected >= {min_count}, got {actual}")
        all_ok = False
    else:
        print(f"  ✅ {table}: {actual} >= {min_count}")

# ============================================================================
# STEP 7: Cleanup test data
# ============================================================================
print("\n[8/8] Cleaning up test data...")
try:
    # Delete in correct order (foreign key constraints)
    db.execute(text(f"DELETE FROM resolutions WHERE ticket_id IN (SELECT id FROM tickets WHERE phone_number='{TEST_PHONE}')"))
    db.execute(text(f"DELETE FROM analytics_data WHERE conversation_id IN (SELECT id FROM conversations WHERE phone_number='{TEST_PHONE}')"))
    db.execute(text(f"DELETE FROM solution_attempts WHERE phone_number='{TEST_PHONE}'"))
    db.execute(text(f"DELETE FROM solution_effectiveness WHERE solution_id='gps' AND category='GPS'"))
    db.execute(text(f"DELETE FROM conversation_turns WHERE phone_number='{TEST_PHONE}'"))
    db.execute(text(f"DELETE FROM message_history WHERE phone_number='{TEST_PHONE}'"))
    db.execute(text(f"DELETE FROM conversation_context WHERE phone_number='{TEST_PHONE}'"))
    db.execute(text(f"DELETE FROM user_profile_data WHERE phone_number='{TEST_PHONE}'"))
    db.execute(text(f"DELETE FROM tickets WHERE phone_number='{TEST_PHONE}'"))
    db.execute(text(f"DELETE FROM conversations WHERE phone_number='{TEST_PHONE}'"))
    db.execute(text(f"DELETE FROM users WHERE phone_number='{TEST_PHONE}'"))
    db.commit()
    print("  ✅ Test data cleaned up")
except Exception as e:
    print(f"  ⚠️ Cleanup error (non-critical): {e}")
    db.rollback()
finally:
    db.close()

# ============================================================================
# FINAL RESULT
# ============================================================================
print("\n" + "=" * 60)
if all_ok:
    print("✅ ALL 13 TABLES VERIFIED - DATABASE INTEGRATION WORKING!")
else:
    print("❌ SOME TABLES HAVE ISSUES - SEE ABOVE")
print("=" * 60)

sys.exit(0 if all_ok else 1)
