"""
Database Tracking Service for TRAMOS WhatsApp Bot
Populates all database tables during conversation flow:
- users: User profiles created/updated on first contact
- conversations: Conversation lifecycle tracking
- message_history: Every message logged
- tickets: Ticket records when created
- resolutions: Resolution tracking when conversation resolves
- analytics_data: Metrics per conversation
- conversation_context: Current context snapshot
- conversation_turns: Turn-by-turn log
- user_profile_data: User behavior tracking
- solution_attempts: KB solution attempts
- solution_effectiveness: Aggregate solution metrics
- dashboard_analytics_summary: Daily summaries
"""

import logging
from contextlib import contextmanager
from datetime import datetime, date
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.config import settings
from app.database_models import (
    DatabaseManager,
    User, Conversation, MessageHistory, Ticket, Resolution,
    AnalyticsData, ConversationContext, ConversationTurn,
    UserProfileData, SolutionAttempt, SolutionEffectiveness,
    ConversationState, MessageSender, TicketStatus, TicketPriority,
    ResolutionType, MetricType,
)

logger = logging.getLogger(__name__)


class DatabaseTracker:
    """
    Centralized database tracking - populates ALL tables during conversation flow.
    Called from whatsapp.py at each dialog state transition.
    """

    def __init__(self):
        self.db_manager: Optional[DatabaseManager] = None

    def init(self, database_url: str):
        """Initialize with database connection"""
        try:
            self.db_manager = DatabaseManager(database_url)
            logger.info("✅ DatabaseTracker initialized")
        except Exception as e:
            logger.error(f"❌ DatabaseTracker init failed: {e}")

    def _get_db(self) -> Optional[Session]:
        if self.db_manager:
            return self.db_manager.get_session()
        return None


    @contextmanager
    def _safe_db(self):
        """Context manager that guarantees session cleanup on any exit path.
        Usage:
            with self._safe_db() as db:
                if db is None:
                    return
                # ... use db ...
        """
        db = self._get_db()
        try:
            yield db
        except Exception:
            if db:
                db.rollback()
            raise
        finally:
            if db:
                db.close()

    # ========================================================================
    # USER MANAGEMENT
    # ========================================================================

    def get_or_create_user(self, phone_number: str, user_name: str = None) -> Optional[int]:
        """Get or create user record. Returns user_id."""
        db = self._get_db()
        if not db:
            return None
        try:
            user = db.query(User).filter_by(phone_number=phone_number).first()
            if not user:
                user = User(
                    phone_number=phone_number,
                    user_name=user_name,
                    language="id",
                    preferred_language="id",
                    first_contact_at=datetime.utcnow(),
                    total_messages=0,
                    total_tickets=0,
                    resolved_tickets=0,
                )
                db.add(user)
                db.commit()
                logger.info(f"👤 New user created: {phone_number}")
            else:
                # Update last contact and name if provided
                user.last_contact_at = datetime.utcnow()
                if user_name and user_name != "User":
                    user.user_name = user_name
                db.commit()

            user_id = user.id
            db.close()
            return user_id
        except Exception as e:
            logger.error(f"❌ get_or_create_user error: {e}")
            db.rollback()
            db.close()
            return None

    def increment_user_messages(self, phone_number: str):
        """Increment total message count for user"""
        db = self._get_db()
        if not db:
            return
        try:
            user = db.query(User).filter_by(phone_number=phone_number).first()
            if user:
                user.total_messages = (user.total_messages or 0) + 1
                user.last_contact_at = datetime.utcnow()
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ increment_user_messages error: {e}")
            db.rollback()
            db.close()

    def increment_user_tickets(self, phone_number: str):
        """Increment total ticket count for user"""
        db = self._get_db()
        if not db:
            return
        try:
            user = db.query(User).filter_by(phone_number=phone_number).first()
            if user:
                user.total_tickets = (user.total_tickets or 0) + 1
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ increment_user_tickets error: {e}")
            db.rollback()
            db.close()

    def update_user_name(self, phone_number: str, driver_name: str):
        """Update user's display name when collected"""
        db = self._get_db()
        if not db:
            return
        try:
            user = db.query(User).filter_by(phone_number=phone_number).first()
            if user and driver_name:
                user.user_name = driver_name
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ update_user_name error: {e}")
            db.rollback()
            db.close()

    # ========================================================================
    # CONVERSATION MANAGEMENT
    # ========================================================================

    def create_conversation(self, phone_number: str, user_id: int) -> Optional[int]:
        """Create new conversation record. Returns conversation_id."""
        db = self._get_db()
        if not db:
            return None
        try:
            conversation = Conversation(
                user_id=user_id,
                phone_number=phone_number,
                current_state=ConversationState.NEW_ISSUE.value,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(conversation)
            db.commit()
            conv_id = conversation.id
            db.close()
            logger.info(f"💬 Conversation #{conv_id} created for {phone_number}")
            return conv_id
        except Exception as e:
            logger.error(f"❌ create_conversation error: {e}")
            db.rollback()
            db.close()
            return None

    def get_or_create_conversation(self, phone_number: str, user_id: int) -> Optional[int]:
        """
        Get existing ACTIVE conversation or create a new one.
        Prevents duplicate conversations when _db_conversation_id is lost
        (e.g. after server restart or session cache miss).
        Returns conversation_id.
        """
        db = self._get_db()
        if not db:
            return None
        try:
            # Look for existing non-closed conversation for this phone
            conv = db.query(Conversation).filter(
                Conversation.phone_number == phone_number,
                Conversation.current_state.notin_([
                    ConversationState.CLOSED.value,
                    ConversationState.RESOLVED.value,
                ])
            ).order_by(Conversation.created_at.desc()).first()

            if conv:
                conv_id = conv.id
                db.close()
                logger.debug(f"💬 Reusing conversation #{conv_id} for {phone_number}")
                return conv_id

            # No active conversation found — create new one
            conversation = Conversation(
                user_id=user_id,
                phone_number=phone_number,
                current_state=ConversationState.NEW_ISSUE.value,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(conversation)
            db.commit()
            conv_id = conversation.id
            db.close()
            logger.info(f"💬 Conversation #{conv_id} created for {phone_number}")
            return conv_id
        except Exception as e:
            logger.error(f"❌ get_or_create_conversation error: {e}")
            db.rollback()
            db.close()
            return None

    def get_active_solution_attempt(self, conversation_id: int) -> Optional[int]:
        """
        Get the most recent unresolved solution attempt for a conversation.
        Used as fallback when _db_solution_attempt_id is lost.
        """
        db = self._get_db()
        if not db:
            return None
        try:
            attempt = db.query(SolutionAttempt).filter(
                SolutionAttempt.conversation_id == conversation_id,
                SolutionAttempt.outcome.is_(None),
            ).order_by(SolutionAttempt.created_at.desc()).first()
            attempt_id = attempt.id if attempt else None
            db.close()
            return attempt_id
        except Exception as e:
            logger.error(f"❌ get_active_solution_attempt error: {e}")
            db.close()
            return None

    def close_conversation(self, conversation_id: int, final_state: str = "closed"):
        """Mark a conversation as closed/resolved in DB"""
        db = self._get_db()
        if not db:
            return
        try:
            conv = db.query(Conversation).filter_by(id=conversation_id).first()
            if conv:
                state_map = {
                    "closed": ConversationState.CLOSED.value,
                    "resolved": ConversationState.RESOLVED.value,
                }
                conv.current_state = state_map.get(final_state, ConversationState.CLOSED.value)
                conv.updated_at = datetime.utcnow()
                conv.last_message_at = datetime.utcnow()
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ close_conversation error: {e}")
            db.rollback()
            db.close()

    def link_ticket_to_conversation(self, conversation_id: int, ticket_id: int):
        """Set ticket_id on the conversation record"""
        db = self._get_db()
        if not db:
            return
        try:
            conv = db.query(Conversation).filter_by(id=conversation_id).first()
            if conv:
                conv.ticket_id = ticket_id
                conv.updated_at = datetime.utcnow()
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ link_ticket_to_conversation error: {e}")
            db.rollback()
            db.close()

    def update_conversation_state(self, conversation_id: int, state: str,
                                   category: str = None, intent: str = None,
                                   issue_description: str = None):
        """Update conversation state and metadata"""
        db = self._get_db()
        if not db:
            return
        try:
            conv = db.query(Conversation).filter_by(id=conversation_id).first()
            if conv:
                # Map dialog states to conversation states
                state_map = {
                    "greeting": ConversationState.NEW_ISSUE.value,
                    "collecting_name": ConversationState.COLLECTING_DETAILS.value,
                    "collecting_problem": ConversationState.COLLECTING_DETAILS.value,
                    "searching_kb_solution": ConversationState.ANALYZING.value,
                    "presenting_solution": ConversationState.OFFERING_SOLUTIONS.value,
                    "asking_solution_worked": ConversationState.USER_TRYING.value,
                    "collecting_unit": ConversationState.ESCALATING.value,
                    "collecting_location": ConversationState.ESCALATING.value,
                    "collecting_time": ConversationState.ESCALATING.value,
                    "collecting_realtime_reference": ConversationState.COLLECTING_DETAILS.value,
                    "confirming_details": ConversationState.ESCALATING.value,
                    "correcting_details": ConversationState.ESCALATING.value,
                    "creating_ticket": ConversationState.HUMAN_SUPPORT.value,
                    "resolved": ConversationState.RESOLVED.value,
                    "closed": ConversationState.CLOSED.value,
                }
                conv.current_state = state_map.get(state, state)
                conv.updated_at = datetime.utcnow()
                conv.last_message_at = datetime.utcnow()
                if category:
                    conv.category = category
                if intent:
                    conv.intent = intent
                if issue_description:
                    conv.issue_description = issue_description
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ update_conversation_state error: {e}")
            db.rollback()
            db.close()

    # ========================================================================
    # MESSAGE HISTORY
    # ========================================================================

    def log_message(self, conversation_id: int, phone_number: str,
                    sender: str, message_text: str,
                    intent: str = None, category: str = None,
                    confidence: int = 0, message_id: str = None):
        """Log a message to message_history table"""
        db = self._get_db()
        if not db:
            return
        try:
            msg = MessageHistory(
                conversation_id=conversation_id,
                phone_number=phone_number,
                sender=sender,
                message_text=message_text[:5000],  # Truncate very long messages
                message_type="text",
                language="id",
                intent=intent,
                category=category,
                confidence=confidence,
                message_id=message_id,
                created_at=datetime.utcnow(),
            )
            db.add(msg)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ log_message error: {e}")
            db.rollback()
            db.close()

    # ========================================================================
    # CONVERSATION TURNS
    # ========================================================================

    def log_turn(self, conversation_id: int, phone_number: str,
                 turn_number: int, user_message: str, bot_response: str,
                 user_intent: str = None, user_category: str = None,
                 bot_state: str = None, turn_type: str = None,
                 processing_time_ms: int = None):
        """Log a conversation turn"""
        db = self._get_db()
        if not db:
            return
        try:
            turn = ConversationTurn(
                conversation_id=conversation_id,
                phone_number=phone_number,
                turn_number=turn_number,
                user_message=user_message[:5000] if user_message else None,
                user_intent=user_intent,
                user_category=user_category,
                bot_response=bot_response[:5000] if bot_response else None,
                bot_state=bot_state,
                turn_type=turn_type,
                processing_time_ms=processing_time_ms,
                created_at=datetime.utcnow(),
            )
            db.add(turn)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ log_turn error: {e}")
            db.rollback()
            db.close()

    # ========================================================================
    # CONVERSATION CONTEXT
    # ========================================================================

    def update_context(self, phone_number: str, state: str,
                       category: str = None, issue_description: str = None,
                       last_intent: str = None, context_data: dict = None):
        """Update or create conversation context snapshot"""
        db = self._get_db()
        if not db:
            return
        try:
            ctx = db.query(ConversationContext).filter_by(phone_number=phone_number).first()
            if not ctx:
                ctx = ConversationContext(
                    phone_number=phone_number,
                    created_at=datetime.utcnow(),
                )
                db.add(ctx)

            ctx.current_state = state
            ctx.category = category
            ctx.issue_description = issue_description
            ctx.last_intent = last_intent
            ctx.context_data = context_data or {}
            ctx.updated_at = datetime.utcnow()
            ctx.last_accessed_at = datetime.utcnow()

            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ update_context error: {e}")
            db.rollback()
            db.close()

    # ========================================================================
    # TICKET TRACKING
    # ========================================================================

    def create_ticket_record(self, user_id: int, phone_number: str,
                              conversation_id: int, osticket_id: int,
                              subject: str, description: str,
                              category: str, priority: str = "medium") -> Optional[int]:
        """Create ticket record in local DB. Returns ticket_id."""
        db = self._get_db()
        if not db:
            return None
        try:
            ticket = Ticket(
                user_id=user_id,
                phone_number=phone_number,
                osticket_id=osticket_id,
                subject=subject,
                description=description[:5000] if description else None,
                category=category or "Service",
                status=TicketStatus.OPEN.value,
                priority=priority,
                conversation_id=conversation_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(ticket)
            db.commit()
            ticket_id = ticket.id
            db.close()
            logger.info(f"🎫 Ticket record #{ticket_id} created (osTicket: {osticket_id})")
            return ticket_id
        except Exception as e:
            logger.error(f"❌ create_ticket_record error: {e}")
            db.rollback()
            db.close()
            return None

    # ========================================================================
    # RESOLUTION TRACKING
    # ========================================================================

    def create_resolution(self, ticket_id: int, resolution_type: str,
                          resolution_notes: str = None,
                          ai_attempted: bool = False,
                          ai_successful: bool = False,
                          resolution_time_minutes: int = None):
        """Create resolution record for a ticket"""
        db = self._get_db()
        if not db:
            return
        try:
            resolution = Resolution(
                ticket_id=ticket_id,
                resolution_type=resolution_type,
                resolution_notes=resolution_notes,
                resolved_at=datetime.utcnow(),
                resolution_time_minutes=resolution_time_minutes,
                ai_attempted=ai_attempted,
                ai_successful=ai_successful,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(resolution)
            db.commit()
            db.close()
            logger.info(f"✅ Resolution created for ticket #{ticket_id}: {resolution_type}")
        except Exception as e:
            logger.error(f"❌ create_resolution error: {e}")
            db.rollback()
            db.close()

    def create_ai_resolution(self, conversation_id: int, phone_number: str,
                              category: str, resolution_notes: str = None,
                              resolution_time_minutes: int = None):
        """Create resolution record for AI-solved issues (no ticket needed)"""
        try:
            # Log analytics for AI resolution (each opens its own session)
            self.log_analytics(
                metric_type=MetricType.AI_SUCCESS_RATE.value,
                metric_value=1.0,
                category=category or "Service",
                conversation_id=conversation_id,
            )
            self.log_analytics(
                metric_type=MetricType.RESOLUTION_TIME.value,
                metric_value=float(resolution_time_minutes or 0),
                category=category or "Service",
                conversation_id=conversation_id,
            )
        except Exception as e:
            logger.error(f"❌ create_ai_resolution error: {e}")

    # ========================================================================
    # SOLUTION ATTEMPTS
    # ========================================================================

    def log_solution_attempt(self, conversation_id: int, phone_number: str,
                              solution_id: str, category: str,
                              problem_description: str,
                              solution_steps: list = None,
                              kb_match_score: float = None,
                              ai_confidence: float = None) -> Optional[int]:
        """Log a KB solution attempt. Returns solution_attempt_id."""
        db = self._get_db()
        if not db:
            return None
        try:
            attempt = SolutionAttempt(
                conversation_id=conversation_id,
                phone_number=phone_number,
                solution_id=solution_id,
                category=category or "Service",
                problem_description=problem_description or "No description",
                solution_steps=solution_steps,
                kb_match_score=kb_match_score,
                ai_confidence=ai_confidence,
                created_at=datetime.utcnow(),
            )
            db.add(attempt)
            db.commit()
            attempt_id = attempt.id
            db.close()
            return attempt_id
        except Exception as e:
            logger.error(f"❌ log_solution_attempt error: {e}")
            db.rollback()
            db.close()
            return None

    def update_solution_outcome(self, attempt_id: int, outcome: str,
                                 user_feedback: str = None,
                                 escalation_needed: bool = False):
        """Update outcome of a solution attempt"""
        db = self._get_db()
        if not db:
            return
        try:
            attempt = db.query(SolutionAttempt).filter_by(id=attempt_id).first()
            if attempt:
                attempt.outcome = outcome  # worked, failed, escalated
                attempt.user_feedback = user_feedback
                attempt.escalation_needed = escalation_needed
                attempt.outcome_recorded_at = datetime.utcnow()
                attempt.updated_at = datetime.utcnow()
                db.commit()

                # Update solution effectiveness aggregate
                self._update_solution_effectiveness(
                    db, attempt.solution_id, attempt.category, outcome
                )
            db.close()
        except Exception as e:
            logger.error(f"❌ update_solution_outcome error: {e}")
            db.rollback()
            db.close()

    def _update_solution_effectiveness(self, db: Session, solution_id: str,
                                        category: str, outcome: str):
        """Update aggregate solution effectiveness metrics"""
        try:
            eff = db.query(SolutionEffectiveness).filter_by(
                solution_id=solution_id, category=category
            ).first()

            if not eff:
                eff = SolutionEffectiveness(
                    solution_id=solution_id,
                    category=category,
                    created_at=datetime.utcnow(),
                )
                db.add(eff)

            eff.total_attempts = (eff.total_attempts or 0) + 1

            if outcome == "worked":
                eff.worked_count = (eff.worked_count or 0) + 1
            elif outcome == "partially_worked":
                eff.partially_worked_count = (eff.partially_worked_count or 0) + 1
            elif outcome == "failed":
                eff.failed_count = (eff.failed_count or 0) + 1
            elif outcome == "escalated":
                eff.escalated_count = (eff.escalated_count or 0) + 1
            elif outcome == "abandoned":
                eff.abandoned_count = (eff.abandoned_count or 0) + 1

            total = eff.total_attempts or 1
            eff.success_rate = ((eff.worked_count or 0) + (eff.partially_worked_count or 0)) / total
            eff.pure_success_rate = (eff.worked_count or 0) / total
            eff.escalation_rate = (eff.escalated_count or 0) / total

            # Health scoring
            if eff.success_rate >= 0.8:
                eff.recommendation = "excellent"
                eff.health_score = 0.9
            elif eff.success_rate >= 0.6:
                eff.recommendation = "good"
                eff.health_score = 0.7
            elif eff.success_rate >= 0.4:
                eff.recommendation = "okay"
                eff.health_score = 0.5
            elif eff.success_rate >= 0.2:
                eff.recommendation = "needs_review"
                eff.health_score = 0.3
            else:
                eff.recommendation = "broken"
                eff.health_score = 0.1

            eff.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            logger.error(f"❌ _update_solution_effectiveness error: {e}")

    # ========================================================================
    # USER PROFILE DATA
    # ========================================================================

    def update_user_profile(self, phone_number: str,
                             category: str = None,
                             issue_resolved: bool = False,
                             is_frustrated: bool = False):
        """Update user profile data for personalization"""
        db = self._get_db()
        if not db:
            return
        try:
            profile = db.query(UserProfileData).filter_by(phone_number=phone_number).first()
            if not profile:
                profile = UserProfileData(
                    phone_number=phone_number,
                    created_at=datetime.utcnow(),
                )
                db.add(profile)

            profile.total_interactions = (profile.total_interactions or 0) + 1
            profile.last_interaction = datetime.utcnow()
            profile.updated_at = datetime.utcnow()

            if issue_resolved:
                profile.completed_issues = (profile.completed_issues or 0) + 1
            else:
                profile.failed_issues = (profile.failed_issues or 0) + 1

            total = (profile.completed_issues or 0) + (profile.failed_issues or 0)
            if total > 0:
                profile.success_rate = (profile.completed_issues or 0) / total

            # Update skill level based on interactions
            interactions = profile.total_interactions or 0
            if interactions >= 20:
                profile.skill_level = "expert"
            elif interactions >= 10:
                profile.skill_level = "advanced"
            elif interactions >= 5:
                profile.skill_level = "intermediate"
            else:
                profile.skill_level = "newbie"

            profile.is_frustrated = is_frustrated

            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ update_user_profile error: {e}")
            db.rollback()
            db.close()

    # ========================================================================
    # ANALYTICS
    # ========================================================================

    def log_analytics(self, metric_type: str, metric_value: float,
                      category: str, conversation_id: int = None,
                      ticket_id: int = None):
        """Log an analytics data point"""
        db = self._get_db()
        if not db:
            return
        try:
            now = datetime.utcnow()
            analytics = AnalyticsData(
                conversation_id=conversation_id,
                ticket_id=ticket_id,
                metric_type=metric_type,
                metric_value=metric_value,
                category=category,
                date_recorded=now.date(),
                hour_recorded=now.hour,
                created_at=now,
            )
            db.add(analytics)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ log_analytics error: {e}")
            db.rollback()
            db.close()

    def update_dashboard_summary(self):
        """Update daily dashboard analytics summary"""
        db = self._get_db()
        if not db:
            return
        try:
            today = date.today()
            from app.database_models import WhatsAppSession

            # Count today's conversations
            total_convs = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= datetime.combine(today, datetime.min.time())
            ).count()

            # Count tickets created today
            total_tickets = db.query(Ticket).filter(
                Ticket.created_at >= datetime.combine(today, datetime.min.time())
            ).count()

            # Count AI resolutions today
            ai_resolved = db.query(AnalyticsData).filter(
                AnalyticsData.date_recorded == today,
                AnalyticsData.metric_type == MetricType.AI_SUCCESS_RATE.value,
                AnalyticsData.metric_value == 1.0,
            ).count()

            ai_rate = ai_resolved / max(total_convs, 1)

            # Calculate average resolution time from today's resolutions
            from sqlalchemy import func
            avg_res_time = db.query(func.avg(Resolution.resolution_time_minutes)).filter(
                Resolution.created_at >= datetime.combine(today, datetime.min.time())
            ).scalar()
            avg_res_time = int(avg_res_time) if avg_res_time else None

            # Get most common category
            common_cat = db.query(
                WhatsAppSession.problem_category,
                func.count(WhatsAppSession.problem_category)
            ).filter(
                WhatsAppSession.created_at >= datetime.combine(today, datetime.min.time()),
                WhatsAppSession.problem_category.isnot(None),
            ).group_by(WhatsAppSession.problem_category).order_by(
                func.count(WhatsAppSession.problem_category).desc()
            ).first()

            # Upsert dashboard summary using ORM approach
            from app.database_models import Base as _  # noqa
            from sqlalchemy import text as sql_text
            
            summary_row = db.execute(
                sql_text("SELECT id FROM dashboard_analytics_summary WHERE summary_date = :today"),
                {"today": str(today)}
            ).first()

            cat_name = common_cat[0] if common_cat else 'N/A'
            
            if summary_row:
                db.execute(
                    sql_text("""UPDATE dashboard_analytics_summary SET
                        total_conversations = :convs,
                        total_tickets_created = :tickets,
                        ai_success_rate = :ai_rate,
                        avg_resolution_time = :avg_res,
                        most_common_category = :cat,
                        created_at = NOW()
                    WHERE summary_date = :today"""),
                    {"convs": total_convs, "tickets": total_tickets, 
                     "ai_rate": round(ai_rate, 4), "avg_res": avg_res_time,
                     "cat": cat_name, "today": str(today)}
                )
            else:
                db.execute(
                    sql_text("""INSERT INTO dashboard_analytics_summary
                        (summary_date, total_conversations, total_tickets_created,
                         ai_success_rate, avg_resolution_time, most_common_category, created_at)
                    VALUES (:today, :convs, :tickets, :ai_rate, :avg_res, :cat, NOW())"""),
                    {"today": str(today), "convs": total_convs, "tickets": total_tickets,
                     "ai_rate": round(ai_rate, 4), "avg_res": avg_res_time, "cat": cat_name}
                )
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"❌ update_dashboard_summary error: {e}")
            try:
                db.rollback()
                db.close()
            except Exception as cleanup_error:
                logger.debug("Dashboard summary cleanup failed: %s", cleanup_error)

    # ========================================================================
    # CONVENIENCE: FULL TURN TRACKING
    # ========================================================================

    def track_full_turn(self, phone_number: str, user_message: str,
                         bot_response: str, conversation_id: int,
                         turn_number: int, current_state: str,
                         intent: str = None, category: str = None,
                         processing_time_ms: int = None):
        """
        One-call method to track a complete conversation turn.
        Logs message_history (user + bot), conversation_turn, and context.
        """
        # Log user message
        self.log_message(
            conversation_id=conversation_id,
            phone_number=phone_number,
            sender="user",
            message_text=user_message,
            intent=intent,
            category=category,
        )

        # Log bot response
        self.log_message(
            conversation_id=conversation_id,
            phone_number=phone_number,
            sender="bot",
            message_text=bot_response,
            intent=intent,
            category=category,
        )

        # Log turn
        self.log_turn(
            conversation_id=conversation_id,
            phone_number=phone_number,
            turn_number=turn_number,
            user_message=user_message,
            bot_response=bot_response,
            user_intent=intent,
            user_category=category,
            bot_state=current_state,
            turn_type=intent or "dialog",
            processing_time_ms=processing_time_ms,
        )

        # Update context
        self.update_context(
            phone_number=phone_number,
            state=current_state,
            category=category,
            last_intent=intent,
        )

        # Update conversation state
        self.update_conversation_state(
            conversation_id=conversation_id,
            state=current_state,
            category=category,
            intent=intent,
        )

        # Increment message count
        self.increment_user_messages(phone_number)


# Global singleton
db_tracker = DatabaseTracker()


def init_db_tracker():
    """Initialize global database tracker"""
    db_tracker.init(settings.DATABASE_URL)
    return db_tracker
