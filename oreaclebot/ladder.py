"""
Ladder monotonicity checker for time-based markets.

Ensures P(YES earlier deadline) ≤ P(YES later deadline) for markets with temporal structure.
This is a fundamental arbitrage constraint that should hold for rational prediction markets.
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import re

from .client import ManifoldClient, Comment


class LadderViolation:
    """Represents a monotonicity violation between two markets."""
    
    def __init__(self, earlier_market: Dict, later_market: Dict, 
                 earlier_prob: float, later_prob: float):
        self.earlier_market = earlier_market
        self.later_market = later_market
        self.earlier_prob = earlier_prob
        self.later_prob = later_prob
        self.violation_size = earlier_prob - later_prob
        
    def __str__(self) -> str:
        return (
            f"Monotonicity violation: "
            f"{self.earlier_market.get('question', 'Unknown')} "
            f"({self.earlier_prob:.1%}) > "
            f"{self.later_market.get('question', 'Unknown')} "
            f"({self.later_prob:.1%}) "
            f"(violation: {self.violation_size:.1%})"
        )


class LadderMonotonicity:
    """
    Checks and enforces monotonicity constraints on temporal market ladders.
    
    For markets asking "Will X happen by date Y?", ensures that:
    P(YES by earlier date) ≤ P(YES by later date)
    """
    
    def __init__(self, client: ManifoldClient, min_violation_size: float = 0.05):
        """
        Initialize ladder checker.
        
        Args:
            client: ManifoldClient for posting comments/trades
            min_violation_size: Minimum violation size to flag (0.05 = 5%)
        """
        self.client = client
        self.min_violation_size = min_violation_size
        self.logger = logging.getLogger(__name__)
        
    def extract_deadline_from_question(self, question: str) -> Optional[datetime]:
        """
        Extract deadline from market question.
        
        Handles patterns like:
        - "Will X happen by 2024-12-31?"
        - "Will X happen by December 31, 2024?"
        - "Will X happen before January 1st?"
        """
        # ISO date pattern (2024-12-31)
        iso_match = re.search(r'by\s+(\d{4}-\d{2}-\d{2})', question, re.IGNORECASE)
        if iso_match:
            try:
                return datetime.strptime(iso_match.group(1), '%Y-%m-%d')
            except ValueError:
                pass
                
        # Month name patterns (December 31, 2024)
        month_pattern = r'by\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})'
        month_match = re.search(month_pattern, question, re.IGNORECASE)
        if month_match:
            try:
                month_str = f"{month_match.group(1)} {month_match.group(2)}, {month_match.group(3)}"
                return datetime.strptime(month_str, '%B %d, %Y')
            except ValueError:
                try:
                    return datetime.strptime(month_str, '%b %d, %Y')
                except ValueError:
                    pass
        
        # "before" patterns - treat as day before
        before_match = re.search(r'before\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})', question, re.IGNORECASE)
        if before_match:
            try:
                date_str = f"{before_match.group(1)} {before_match.group(2)}, {before_match.group(3)}"
                base_date = datetime.strptime(date_str, '%B %d, %Y')
                return base_date - timedelta(days=1)
            except ValueError:
                pass
                
        return None
    
    def group_markets_by_base_question(self, markets: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group markets by their base question (removing date references).
        
        Returns dict mapping base questions to list of markets with different deadlines.
        """
        groups = {}
        
        for market in markets:
            question = market.get('question', '')
            
            # Extract base question by removing date-specific parts
            base_question = re.sub(r'\s*(by|before)\s+[^?]+', '', question, flags=re.IGNORECASE)
            base_question = base_question.strip()
            
            if base_question not in groups:
                groups[base_question] = []
            groups[base_question].append(market)
            
        # Only return groups with multiple markets
        return {k: v for k, v in groups.items() if len(v) > 1}
    
    def check_group_monotonicity(self, markets: List[Dict]) -> List[LadderViolation]:
        """
        Check monotonicity within a group of related markets.
        
        Returns list of violations found.
        """
        violations = []
        
        # Extract deadlines and sort by date
        markets_with_deadlines = []
        for market in markets:
            deadline = self.extract_deadline_from_question(market.get('question', ''))
            if deadline:
                markets_with_deadlines.append((market, deadline))
        
        # Sort by deadline
        markets_with_deadlines.sort(key=lambda x: x[1])
        
        # Check monotonicity constraint
        for i in range(len(markets_with_deadlines)):
            for j in range(i + 1, len(markets_with_deadlines)):
                earlier_market, earlier_date = markets_with_deadlines[i]
                later_market, later_date = markets_with_deadlines[j]
                
                earlier_prob = earlier_market.get('probability', 0)
                later_prob = later_market.get('probability', 0)
                
                # Check violation: P(earlier) > P(later)
                if earlier_prob > later_prob + self.min_violation_size:
                    violation = LadderViolation(
                        earlier_market, later_market, 
                        earlier_prob, later_prob
                    )
                    violations.append(violation)
                    
        return violations
    
    def check_all_violations(self, markets: List[Dict]) -> List[LadderViolation]:
        """
        Check all monotonicity violations across all market groups.
        
        Args:
            markets: List of market data from Manifold API
            
        Returns:
            List of all violations found
        """
        all_violations = []
        
        groups = self.group_markets_by_base_question(markets)
        
        for base_question, group_markets in groups.items():
            self.logger.debug(f"Checking monotonicity for: {base_question} ({len(group_markets)} markets)")
            violations = self.check_group_monotonicity(group_markets)
            all_violations.extend(violations)
            
        return all_violations
    
    def create_violation_comment(self, violation: LadderViolation) -> str:
        """
        Create a comment explaining the monotonicity violation.
        
        Returns formatted comment text.
        """
        comment = f"""🚨 **Monotonicity Violation Detected**

**Issue**: Earlier deadline has higher probability than later deadline
- **Earlier market**: {violation.earlier_market.get('question', 'Unknown')} → **{violation.earlier_prob:.1%}**
- **Later market**: {violation.later_market.get('question', 'Unknown')} → **{violation.later_prob:.1%}**

**Violation size**: {violation.violation_size:.1%}

This violates the fundamental constraint that P(event by earlier date) ≤ P(event by later date).

*This comment was generated by Oreacle Bot's ladder monotonicity checker.*
"""
        return comment
    
    def post_violation_comments(self, violations: List[LadderViolation], 
                              dry_run: bool = False) -> int:
        """
        Post comments about violations to the relevant markets.
        
        Args:
            violations: List of violations to comment on
            dry_run: If True, only log what would be posted
            
        Returns:
            Number of comments posted
        """
        comments_posted = 0
        
        for violation in violations:
            comment_text = self.create_violation_comment(violation)
            
            if dry_run:
                self.logger.info(f"DRY RUN - Would post to {violation.earlier_market.get('slug')}: {comment_text[:100]}...")
                continue
                
            try:
                # Post to the earlier market (the one with inflated probability)
                market_id = violation.earlier_market.get('id')
                if market_id:
                    comment = Comment(contractId=market_id, content=comment_text)
                    response = self.client.post_comment(comment)
                    self.logger.info(f"Posted violation comment to market {market_id}")
                    comments_posted += 1
                else:
                    self.logger.warning(f"No market ID found for violation: {violation}")
                    
            except Exception as e:
                self.logger.error(f"Failed to post violation comment: {e}")
                
        return comments_posted
    
    def run_monotonicity_check(self, markets: List[Dict] = None, 
                             dry_run: bool = True) -> Dict[str, int]:
        """
        Run full monotonicity check pipeline.
        
        Args:
            markets: List of markets to check (fetches if None)
            dry_run: If True, only logs violations without posting comments
            
        Returns:
            Dict with 'violations_found' and 'comments_posted' counts
        """
        if markets is None:
            # Fetch markets from Manifold (would need to implement search)
            self.logger.warning("Market fetching not implemented - need markets parameter")
            return {'violations_found': 0, 'comments_posted': 0}
            
        violations = self.check_all_violations(markets)
        
        self.logger.info(f"Found {len(violations)} monotonicity violations")
        for violation in violations:
            self.logger.warning(str(violation))
            
        comments_posted = self.post_violation_comments(violations, dry_run=dry_run)
        
        return {
            'violations_found': len(violations),
            'comments_posted': comments_posted
        }


def run_cli():
    """CLI entry point for ladder monotonicity checking - only for direct execution."""
    import os
    import argparse
    
    parser = argparse.ArgumentParser(description="Check market ladder monotonicity")
    parser.add_argument("--dry-run", action="store_true", help="Only log violations, don't post comments")
    parser.add_argument("--min-violation", type=float, default=0.05, help="Minimum violation size to flag")
    args = parser.parse_args()
    
    # Initialize client
    api_key = os.environ.get("MANIFOLD_API_KEY")
    if not api_key:
        print("Error: MANIFOLD_API_KEY environment variable required")
        return 1
        
    client = ManifoldClient(api_key)
    checker = LadderMonotonicity(client, min_violation_size=args.min_violation)
    
    # For now, would need to implement market search to get relevant markets
    print("Note: Market fetching not implemented - pass markets list to run_monotonicity_check()")
    
    return 0


def main():
    """Main function for CLI integration - no argument parsing."""
    import os
    
    # Initialize client
    api_key = os.environ.get("MANIFOLD_API_KEY")
    if not api_key:
        print("Error: MANIFOLD_API_KEY environment variable required")
        return 1
        
    client = ManifoldClient(api_key)
    checker = LadderMonotonicity(client, min_violation_size=0.05)
    
    # For now, would need to implement market search to get relevant markets
    print("Note: Market fetching not implemented - pass markets list to run_monotonicity_check()")
    
    return 0


if __name__ == "__main__":
    exit(run_cli())