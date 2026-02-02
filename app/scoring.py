import logging
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class ScoringService:
    """Deterministic scoring service."""
    
    def __init__(
        self,
        threshold: float = None,
        hold_band: float = None
    ):
        self.threshold = threshold or settings.scoring_threshold
        self.hold_band = hold_band or settings.scoring_hold_band
    
    def compute_score(
        self,
        evaluations: List[Dict[str, Any]],
        must_have_gating: bool = True
    ) -> Dict[str, Any]:
        """
        Compute deterministic score from evaluations.
        
        Returns:
            {
                "score": float (0-1),
                "decision": "pass"|"hold"|"reject",
                "audit_trail": {...}
            }
        """
        if not evaluations:
            return {
                "score": 0.0,
                "decision": "reject",
                "audit_trail": {
                    "error": "No evaluations provided"
                }
            }
        
        # Normalize weights (sum to 1.0)
        total_weight = sum(eval.get("weight", 0.0) for eval in evaluations)
        if total_weight == 0:
            # Equal weights if none provided
            weight_per_req = 1.0 / len(evaluations)
            for eval in evaluations:
                eval["weight"] = weight_per_req
        else:
            # Normalize
            for eval in evaluations:
                eval["weight"] = eval.get("weight", 0.0) / total_weight
        
        # Check must-have gating
        must_have_failed = False
        if must_have_gating:
            must_haves = [e for e in evaluations if e.get("category") == "must"]
            for must_have in must_haves:
                rating = must_have.get("rating", 0.0)
                if rating < 1.0:
                    must_have_failed = True
                    logger.info(f"Must-have requirement failed: {must_have.get('requirement_text', 'Unknown')}")
                    break
        
        # Compute weighted score
        weighted_sum = sum(
            eval.get("rating", 0.0) * eval.get("weight", 0.0)
            for eval in evaluations
        )
        
        score = max(0.0, min(1.0, weighted_sum))  # Clamp to [0, 1]
        
        # Determine decision
        if must_have_failed:
            decision = "reject"
        elif score >= self.threshold:
            decision = "pass"
        elif score >= (self.threshold - self.hold_band):
            decision = "hold"
        else:
            decision = "reject"
        
        # Build audit trail
        audit_trail = {
            "threshold": self.threshold,
            "hold_band": self.hold_band,
            "must_have_gating": must_have_gating,
            "must_have_failed": must_have_failed,
            "weighted_sum": weighted_sum,
            "score": score,
            "decision": decision,
            "evaluation_details": [
                {
                    "requirement": eval.get("requirement_text", ""),
                    "category": eval.get("category", ""),
                    "weight": eval.get("weight", 0.0),
                    "rating": eval.get("rating", 0.0),
                    "contribution": eval.get("rating", 0.0) * eval.get("weight", 0.0)
                }
                for eval in evaluations
            ]
        }
        
        return {
            "score": score,
            "decision": decision,
            "audit_trail": audit_trail
        }
    
    def extract_strengths_and_gaps(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Extract strengths and gaps from evaluations."""
        strengths = []
        gaps = []
        
        for eval in evaluations:
            req_text = eval.get("requirement_text", "")
            rating = eval.get("rating", 0.0)
            category = eval.get("category", "")
            
            if rating >= 1.0:
                strengths.append(f"{req_text} (Fully met)")
            elif rating >= 0.5:
                strengths.append(f"{req_text} (Partially met)")
            else:
                if category == "must":
                    gaps.append(f"{req_text} (Must-have - Not met)")
                else:
                    gaps.append(f"{req_text} (Not met)")
        
        return {
            "strengths": strengths,
            "gaps": gaps
        }
