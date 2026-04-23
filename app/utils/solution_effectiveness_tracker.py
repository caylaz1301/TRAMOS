"""
Solution Effectiveness Tracker - Measure & improve solution quality
Tracks which solutions actually work for users, enabling continuous improvement
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SolutionOutcome(str, Enum):
    """Possible outcomes of a solution attempt"""
    WORKED = "worked"
    PARTIALLY_WORKED = "partially_worked"
    FAILED = "failed"
    ABANDONED = "abandoned"  # User gave up
    ESCALATED = "escalated"  # Needed human support


class SolutionEffectivenessTracker:
    """
    Track effectiveness of every solution provided.
    Enables data-driven improvement of troubleshooting quality.
    """
    
    def __init__(self):
        self.solution_attempts: List[Dict] = []
        self.solution_stats: Dict[str, Dict] = {}
        logger.info("✅ Solution Effectiveness Tracker initialized")
    
    def log_solution_attempt(
        self,
        solution_id: str,
        category: str,
        user_phone: str,
        solution_description: str,
        user_attempt_count: int = 1,
        resolution_time_minutes: int = 0
    ) -> Dict:
        """
        Log that we've provided a solution to a user.
        
        Args:
            solution_id: Unique ID for this solution (e.g., KB_GPS_001)
            category: Problem category
            user_phone: User's phone number
            solution_description: What was the solution about
            user_attempt_count: How many attempts user has made
            resolution_time_minutes: How long user has been troubleshooting
        
        Returns:
            Attempt record
        """
        attempt = {
            'attempt_id': f"{solution_id}_{user_phone}_{datetime.utcnow().timestamp()}",
            'solution_id': solution_id,
            'category': category,
            'user_phone': user_phone,
            'solution_description': solution_description,
            'provided_at': datetime.utcnow().isoformat(),
            'user_attempt_count': user_attempt_count,
            'resolution_time_minutes': resolution_time_minutes,
            'outcome': None,  # Will be set later
            'outcome_recorded_at': None,
        }
        
        self.solution_attempts.append(attempt)
        return attempt
    
    def record_solution_outcome(
        self,
        attempt_id: str,
        outcome: SolutionOutcome,
        user_feedback: Optional[str] = None,
        actual_resolution_time_minutes: Optional[int] = None
    ) -> bool:
        """
        Record the outcome of a solution attempt.
        
        Args:
            attempt_id: ID of solution attempt from log_solution_attempt
            outcome: Whether it worked, partially worked, failed, etc
            user_feedback: Optional feedback from user
            actual_resolution_time_minutes: Actual time to resolve
        
        Returns:
            True if successfully recorded
        """
        # Find attempt
        attempt = next(
            (a for a in self.solution_attempts if a['attempt_id'] == attempt_id),
            None
        )
        
        if not attempt:
            logger.warning(f"⚠️ Solution attempt not found: {attempt_id}")
            return False
        
        # Handle both SolutionOutcome enum and strings
        outcome_value = outcome.value if isinstance(outcome, SolutionOutcome) else str(outcome)
        
        # Record outcome
        attempt['outcome'] = outcome_value
        attempt['outcome_recorded_at'] = datetime.utcnow().isoformat()
        attempt['user_feedback'] = user_feedback
        attempt['actual_resolution_time_minutes'] = actual_resolution_time_minutes
        
        # Update statistics
        self._update_statistics(attempt)
        
        logger.info(f"📊 Recorded solution outcome: {attempt['solution_id']} → {outcome_value}")
        
        return True
    
    def _update_statistics(self, attempt: Dict):
        """Update effectiveness statistics for this solution"""
        solution_id = attempt['solution_id']
        
        if solution_id not in self.solution_stats:
            self.solution_stats[solution_id] = {
                'category': attempt['category'],
                'total_attempts': 0,
                'successful': 0,
                'partially_successful': 0,
                'failed': 0,
                'abandoned': 0,
                'escalated': 0,
                'avg_resolution_time': 0,
                'resolution_times': [],
            }
        
        stats = self.solution_stats[solution_id]
        stats['total_attempts'] += 1
        
        # Count outcome
        outcome = attempt['outcome']
        if outcome == 'worked':
            stats['successful'] += 1
        elif outcome == 'partially_worked':
            stats['partially_successful'] += 1
        elif outcome == 'failed':
            stats['failed'] += 1
        elif outcome == 'abandoned':
            stats['abandoned'] += 1
        elif outcome == 'escalated':
            stats['escalated'] += 1
        
        # Track resolution time
        if attempt.get('actual_resolution_time_minutes'):
            stats['resolution_times'].append(attempt['actual_resolution_time_minutes'])
            stats['avg_resolution_time'] = (
                sum(stats['resolution_times']) / len(stats['resolution_times'])
            )
    
    def get_solution_effectiveness(self, solution_id: str) -> Dict:
        """
        Get effectiveness metrics for a specific solution.
        
        Returns:
            {
                'success_rate': 0.0-1.0,
                'partial_success_rate': 0.0-1.0,
                'failure_rate': 0.0-1.0,
                'escalation_rate': 0.0-1.0,
                'avg_resolution_time': minutes,
                'recommendation': 'good'|'okay'|'needs_improvement'|'broken',
            }
        """
        if solution_id not in self.solution_stats:
            return {
                'status': 'no_data',
                'solution_id': solution_id,
            }
        
        stats = self.solution_stats[solution_id]
        total = stats['total_attempts']
        
        if total == 0:
            return {
                'status': 'no_data',
                'solution_id': solution_id,
            }
        
        success_rate = stats['successful'] / total
        failure_rate = stats['failed'] / total
        escalation_rate = stats['escalated'] / total
        
        # Determine recommendation
        if success_rate >= 0.8:
            recommendation = 'excellent'
        elif success_rate >= 0.6:
            recommendation = 'good'
        elif success_rate >= 0.4:
            recommendation = 'okay'
        elif escalation_rate > 0.3:
            recommendation = 'needs_review'
        else:
            recommendation = 'broken'
        
        return {
            'status': 'success',
            'solution_id': solution_id,
            'category': stats['category'],
            'total_attempts': total,
            'success_rate': success_rate,
            'partial_success_rate': stats['partially_successful'] / total,
            'failure_rate': failure_rate,
            'escalation_rate': escalation_rate,
            'avg_resolution_time_minutes': stats['avg_resolution_time'],
            'recommendation': recommendation,
            'health_score': (success_rate * 0.6 + (1 - escalation_rate) * 0.4),  # 0-1
        }
    
    def get_category_effectiveness(self, category: str) -> Dict:
        """
        Get effectiveness metrics for all solutions in a category.
        """
        category_stats = {s: stat for s, stat in self.solution_stats.items() 
                         if stat['category'] == category}
        
        if not category_stats:
            return {'status': 'no_data', 'category': category}
        
        total_attempts = sum(s['total_attempts'] for s in category_stats.values())
        total_successful = sum(s['successful'] for s in category_stats.values())
        total_escalated = sum(s['escalated'] for s in category_stats.values())
        
        avg_times = [
            s['avg_resolution_time'] 
            for s in category_stats.values() 
            if s['avg_resolution_time'] > 0
        ]
        
        return {
            'status': 'success',
            'category': category,
            'total_solutions': len(category_stats),
            'total_attempts': total_attempts,
            'category_success_rate': total_successful / total_attempts if total_attempts > 0 else 0,
            'category_escalation_rate': total_escalated / total_attempts if total_attempts > 0 else 0,
            'avg_resolution_time': sum(avg_times) / len(avg_times) if avg_times else 0,
            'solutions': {
                sol_id: self.get_solution_effectiveness(sol_id)
                for sol_id in category_stats.keys()
            }
        }
    
    def get_top_performing_solutions(self, limit: int = 10) -> List[Dict]:
        """
        Get top performing solutions by success rate.
        Useful for promoting best solutions.
        """
        solutions_with_stats = [
            (sol_id, self.get_solution_effectiveness(sol_id))
            for sol_id in self.solution_stats.keys()
        ]
        
        # Filter by minimum attempts (statistical significance)
        significant = [
            (sol_id, stats) 
            for sol_id, stats in solutions_with_stats
            if stats.get('total_attempts', 0) >= 5
        ]
        
        # Sort by health score
        significant.sort(
            key=lambda x: x[1].get('health_score', 0),
            reverse=True
        )
        
        return [sol_id for sol_id, _ in significant[:limit]]
    
    def get_problematic_solutions(self, threshold: float = 0.4) -> List[Dict]:
        """
        Identify solutions with low success rates.
        These need review or improvement.
        """
        problematic = []
        
        for sol_id, stats in self.solution_stats.items():
            if stats['total_attempts'] < 3:  # Need minimum data
                continue
            
            effectiveness = self.get_solution_effectiveness(sol_id)
            
            if effectiveness.get('success_rate', 1.0) < threshold:
                problematic.append({
                    'solution_id': sol_id,
                    'category': stats['category'],
                    'success_rate': effectiveness['success_rate'],
                    'attempts': stats['total_attempts'],
                    'escalation_rate': effectiveness['escalation_rate'],
                    'recommendation': effectiveness['recommendation'],
                })
        
        # Sort by worst first
        problematic.sort(key=lambda x: x['success_rate'])
        return problematic
    
    def get_performance_report(self) -> Dict:
        """
        Generate comprehensive performance report.
        """
        if not self.solution_stats:
            return {'status': 'no_data'}
        
        total_attempts = sum(s['total_attempts'] for s in self.solution_stats.values())
        total_successful = sum(s['successful'] for s in self.solution_stats.values())
        total_escalated = sum(s['escalated'] for s in self.solution_stats.values())
        
        categories = set(s['category'] for s in self.solution_stats.values())
        
        return {
            'status': 'success',
            'summary': {
                'total_solution_attempts': total_attempts,
                'overall_success_rate': total_successful / total_attempts if total_attempts > 0 else 0,
                'overall_escalation_rate': total_escalated / total_attempts if total_attempts > 0 else 0,
                'categories_tracked': list(categories),
                'solutions_tracked': len(self.solution_stats),
            },
            'by_category': {
                cat: self.get_category_effectiveness(cat)
                for cat in sorted(categories)
            },
            'top_performers': self.get_top_performing_solutions(5),
            'needs_attention': self.get_problematic_solutions(0.5),
        }
    
    # ========================================================================
    # FEEDBACK AGGREGATION
    # ========================================================================
    
    def aggregate_solution_feedback(self, solution_id: str, recent_attempts: int = 10) -> Dict:
        """
        Aggregate recent feedback for a specific solution.
        Useful for identifying trends and user sentiment.
        
        Args:
            solution_id: Solution to analyze
            recent_attempts: Number of recent attempts to analyze
        
        Returns:
            Feedback aggregation with trends and recommendations
        """
        # Find recent attempts for this solution
        recent = [
            a for a in self.solution_attempts
            if a['solution_id'] == solution_id and a['outcome']
        ][-recent_attempts:]
        
        if not recent:
            return {'status': 'no_data', 'solution_id': solution_id}
        
        outcomes = [a['outcome'] for a in recent]
        
        return {
            'solution_id': solution_id,
            'recent_attempts': len(recent),
            'outcome_breakdown': {
                'worked': outcomes.count('worked'),
                'partially_worked': outcomes.count('partially_worked'),
                'failed': outcomes.count('failed'),
                'abandoned': outcomes.count('abandoned'),
                'escalated': outcomes.count('escalated'),
            },
            'success_trend': (
                'improving' if self._is_trend_improving(outcomes) else
                'declining' if self._is_trend_declining(outcomes) else
                'stable'
            ),
            'user_feedback': [
                a.get('user_feedback') for a in recent 
                if a.get('user_feedback')
            ],
        }
    
    def _is_trend_improving(self, outcomes: List[str]) -> bool:
        """Check if recent outcomes trending positive"""
        if len(outcomes) < 2:
            return False
        first_half_success = outcomes[:len(outcomes)//2].count('worked')
        second_half_success = outcomes[len(outcomes)//2:].count('worked')
        return second_half_success > first_half_success
    
    def _is_trend_declining(self, outcomes: List[str]) -> bool:
        """Check if recent outcomes trending negative"""
        if len(outcomes) < 2:
            return False
        first_half_success = outcomes[:len(outcomes)//2].count('worked')
        second_half_success = outcomes[len(outcomes)//2:].count('worked')
        return first_half_success > second_half_success
    
    def get_category_feedback_summary(self, category: str) -> Dict:
        """
        Summarize feedback and effectiveness for entire category.
        Helps identify category strengths/weaknesses.
        """
        category_solutions = [
            sol_id for sol_id, stats in self.solution_stats.items()
            if stats['category'] == category
        ]
        
        if not category_solutions:
            return {'status': 'no_data', 'category': category}
        
        total_success = sum(
            self.solution_stats[sol]['successful']
            for sol in category_solutions
        )
        total_attempts = sum(
            self.solution_stats[sol]['total_attempts']
            for sol in category_solutions
        )
        
        return {
            'category': category,
            'solutions_in_category': len(category_solutions),
            'total_attempts': total_attempts,
            'success_rate': total_success / total_attempts if total_attempts > 0 else 0,
            'recommendation': self._rate_category(total_success, total_attempts),
        }
    
    def _rate_category(self, successful: int, total: int) -> str:
        """Rate category quality based on success"""
        if total == 0:
            return 'insufficient_data'
        rate = successful / total
        if rate >= 0.8:
            return '⭐⭐⭐⭐⭐'  # Excellent
        elif rate >= 0.6:
            return '⭐⭐⭐⭐'    # Good
        elif rate >= 0.4:
            return '⭐⭐⭐'      # Fair
        else:
            return '⭐⭐'        # Needs work


# Singleton instance
solution_tracker = SolutionEffectivenessTracker()
