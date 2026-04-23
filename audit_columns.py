"""Audit which columns in each table are written by db_tracker vs never written."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.database_tracker import db_tracker, init_db_tracker
from app.database_models import *
from sqlalchemy import text, inspect as sa_inspect

init_db_tracker()
db = db_tracker._get_db()
engine = db_tracker.db_manager.engine
inspector = sa_inspect(engine)

print("=== TABLE ROW COUNTS ===")
for t in sorted(inspector.get_table_names()):
    count = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
    print(f"  {t:40s} {count} rows")

print("\n=== NEVER-WRITTEN COLUMNS PER TABLE ===\n")

# Auto-managed = id, created_at, updated_at (filled by DB defaults/ORM)
auto = {"id", "created_at", "updated_at"}

checks = {
    "users": ["phone_number","user_name","language","preferred_language",
              "first_contact_at","total_messages","total_tickets","resolved_tickets",
              "last_contact_at"],
    "conversations": ["user_id","phone_number","current_state","category","intent",
                       "issue_description","last_message_at","ticket_id"],
    "message_history": ["conversation_id","phone_number","sender","message_text",
                         "message_type","language","intent","category","confidence",
                         "message_id"],
    "tickets": ["user_id","phone_number","osticket_id","subject","description",
                "category","status","priority","conversation_id"],
    "resolutions": ["ticket_id","resolution_type","resolution_notes","resolved_at",
                    "resolution_time_minutes","ai_attempted","ai_successful"],
    "analytics_data": ["conversation_id","ticket_id","metric_type","metric_value",
                       "category","date_recorded","hour_recorded"],
    "conversation_context": ["phone_number","context_data","current_state","category",
                              "issue_description","last_intent","last_accessed_at"],
    "conversation_turns": ["conversation_id","phone_number","turn_number","user_message",
                            "user_intent","user_category","bot_response","bot_state",
                            "processing_time_ms","turn_type"],
    "user_profile_data": ["phone_number","total_interactions","completed_issues",
                           "failed_issues","success_rate","skill_level","is_frustrated",
                           "last_interaction"],
    "solution_attempts": ["conversation_id","phone_number","solution_id","category",
                           "problem_description","solution_steps","kb_match_score",
                           "ai_confidence","outcome","user_feedback","escalation_needed",
                           "outcome_recorded_at"],
    "solution_effectiveness": ["solution_id","category","total_attempts","worked_count",
                                "partially_worked_count","failed_count","abandoned_count",
                                "escalated_count","success_rate","pure_success_rate",
                                "escalation_rate","health_score","recommendation"],
    "dashboard_analytics_summary": ["summary_date","total_conversations",
                                     "total_tickets_created","ai_success_rate",
                                     "avg_resolution_time","most_common_category"],
    "whatsapp_sessions": ["session_id","phone_number","current_state","is_active",
                           "driver_name","problem_description","problem_category",
                           "problem_severity","vehicle_unit","location","issue_time",
                           "message_count","conversation_history","ticket_created",
                           "ticket_id","osticket_id",
                           "last_activity","expires_at","closed_at"],
}

total_written = 0
total_never = 0
total_auto = 0

for table, written_cols in checks.items():
    db_cols = [c["name"] for c in inspector.get_columns(table)]
    written_set = set(written_cols)
    never = [c for c in db_cols if c not in written_set and c not in auto]
    total_written += len(written_set)
    total_never += len(never)
    total_auto += len([c for c in db_cols if c in auto])
    
    if never:
        print(f"  {table}: {never}")
    else:
        print(f"  {table}: ALL COVERED ✅")

total_cols = total_written + total_never + total_auto
print(f"\n=== SUMMARY ===")
print(f"  Total columns:     {total_cols}")
print(f"  Auto-managed:      {total_auto} (id/created_at/updated_at)")
print(f"  Written by code:   {total_written}")
print(f"  NEVER written:     {total_never}")
coverage = total_written / (total_written + total_never) * 100 if (total_written + total_never) else 100
print(f"  Coverage:          {coverage:.1f}%")

db.close()
