"""
Critique Engine - Multi-LLM critique workflow for validating findings
"""
from typing import List, Dict, Any, Optional
from app.services.llm_client import get_llm_client
from app.services.cost_tracker import CostTracker
from app.config import get_settings
from app.utils.logger import get_logger
import asyncio

logger = get_logger(__name__)


CRITIQUE_SYSTEM_PROMPT = """You are a compliance auditor reviewing another model's finding for accuracy and validity.

Your job is to:
1. Verify the finding is a REAL compliance gap, not a hallucination
2. Check if the regulation reference is correct and applicable
3. Assess if the severity/confidence level is appropriate
4. Identify any corrections needed

Be critical but fair. Only discard findings that are clearly incorrect or irrelevant."""


CRITIQUE_USER_PROMPT = """Review this compliance finding:

**Finding:**
{finding_description}

**Evidence:**
{finding_evidence}

**Regulation Reference:**
{regulation_ref}

**Document Context:**
{document_excerpt}

**Available Regulations:**
{regulation_context}

IMPORTANT: Return ONLY valid JSON. Do not use markdown code blocks or any other formatting.

Your response must be a valid JSON object with this exact structure:
{{
    "status": "verified|needs_correction|discard",
    "reasoning": "Detailed explanation of your assessment",
    "corrections": {{
        "description": "corrected description if needed",
        "regulation_ref": "corrected reference if needed",
        "confidence_adjustment": 0.0
    }},
    "hallucination_detected": false,
    "evidence_valid": true
}}

Notes:
- status must be one of: verified, needs_correction, or discard
- confidence_adjustment is a number between -0.2 and 0.2
- hallucination_detected and evidence_valid must be boolean values (true or false)
- All property names must be in double quotes
- String values must be in double quotes (not single quotes)
"""


class CritiqueEngine:
    """
    Implements the Proposer → Critic → Refiner workflow for validating findings
    """
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.settings = get_settings()
    
    async def critique_finding(
        self,
        finding: Dict[str, Any],
        regulations: str,
        document_context: str,
        cost_tracker: Optional[CostTracker] = None,
    ) -> Dict[str, Any]:
        """
        Critique a single finding
        
        Args:
            finding: The finding to critique
            regulations: Relevant regulation texts
            document_context: Document excerpt for context
            
        Returns:
            {
                "status": "verified|corrected|discarded",
                "refined_finding": {...},
                "critique_trail": [{step, model, reasoning}]
            }
        """
        # Determine critic model
        critic_model = self._get_critic_model(finding.get('model_name'))
        
        if not critic_model:
            logger.warning("No critic model available, skipping critique")
            return {
                "status": "verified",
                "refined_finding": finding,
                "critique_trail": []
            }
        
        # Build critique prompt
        user_prompt = CRITIQUE_USER_PROMPT.format(
            finding_description=finding.get('description', ''),
            finding_evidence=finding.get('evidence', ''),
            regulation_ref=finding.get('regulation_ref', 'None specified'),
            document_excerpt=document_context[:1000],  # Limit context size
            regulation_context=regulations[:2000]  # Limit regulation size
        )
        
        try:
            # Call critic model
            critique_response = await self.llm_client.call_llm(
                model_key=critic_model,
                system_prompt=CRITIQUE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_format="json",
                cost_tracker=cost_tracker,
                phase="critique",
            )
            
            critique_result = critique_response.get('response', {})
            if isinstance(critique_result, str):
                import json
                try:
                    critique_result = json.loads(critique_result)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse critique response as JSON")
                    critique_result = {"status": "verified"}
            
            # Process critique result
            status = critique_result.get('status', 'verified')
            
            # Build critique trail
            critique_trail = [{
                "step": "critique",
                "model": critic_model,
                "proposer_model": finding.get('model_name', 'unknown'),
                "reasoning": critique_result.get('reasoning', ''),
                "hallucination_detected": critique_result.get('hallucination_detected', False),
                "evidence_valid": critique_result.get('evidence_valid', True)
            }]
            
            # Refine finding if corrections needed
            refined_finding = finding.copy()
            
            if status == "discard":
                return {
                    "status": "discarded",
                    "refined_finding": None,
                    "critique_trail": critique_trail
                }
            
            elif status == "needs_correction":
                corrections = critique_result.get('corrections', {})
                
                # Apply corrections
                if corrections.get('description'):
                    refined_finding['description'] = corrections['description']
                if corrections.get('regulation_ref'):
                    refined_finding['regulation_ref'] = corrections['regulation_ref']
                
                # Adjust confidence
                confidence_adj = corrections.get('confidence_adjustment', 0.0)
                original_conf = refined_finding.get('confidence', 0.75)
                refined_finding['confidence'] = max(0.0, min(1.0, original_conf + confidence_adj))
                
                critique_trail[0]['corrections_applied'] = corrections
                
                return {
                    "status": "corrected",
                    "refined_finding": refined_finding,
                    "critique_trail": critique_trail
                }
            
            else:  # verified
                # Optionally boost confidence slightly for verified findings
                if critique_result.get('evidence_valid'):
                    original_conf = refined_finding.get('confidence', 0.75)
                    refined_finding['confidence'] = min(1.0, original_conf + 0.05)
                
                return {
                    "status": "verified",
                    "refined_finding": refined_finding,
                    "critique_trail": critique_trail
                }
                
        except Exception as e:
            logger.error(f"Error during critique: {e}", exc_info=True)
            # On error, return original finding
            return {
                "status": "verified",
                "refined_finding": finding,
                "critique_trail": [{
                    "step": "critique_error",
                    "error": str(e)
                }]
            }
    
    async def critique_batch(
        self,
        findings: List[Dict[str, Any]],
        regulations: str,
        document_context: str,
        cost_tracker: Optional[CostTracker] = None,
    ) -> List[Dict[str, Any]]:
        """
        Critique multiple findings in parallel
        
        Args:
            findings: List of findings to critique
            regulations: Relevant regulation texts
            document_context: Document excerpt for context
            
        Returns:
            List of critique results
        """
        if not self.settings.enable_critique_system:
            logger.info("Critique system disabled, returning findings as-is")
            return [
                {
                    "status": "verified",
                    "refined_finding": finding,
                    "critique_trail": []
                }
                for finding in findings
            ]
        
        logger.info(f"Critiquing {len(findings)} findings")
        
        # Create tasks for parallel critique
        tasks = [
            self.critique_finding(finding, regulations, document_context, cost_tracker=cost_tracker)
            for finding in findings
        ]
        
        # Run critiques in parallel with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(3)  # Max 3 parallel critiques
        
        async def bounded_critique(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(*[bounded_critique(task) for task in tasks])
        
        # Log summary
        verified = sum(1 for r in results if r['status'] == 'verified')
        corrected = sum(1 for r in results if r['status'] == 'corrected')
        discarded = sum(1 for r in results if r['status'] == 'discarded')
        
        logger.info(
            f"Critique complete: {verified} verified, {corrected} corrected, {discarded} discarded"
        )
        
        return results
    
    def _get_critic_model(self, proposer_model: Optional[str] = None) -> Optional[str]:
        """
        Determine which model to use as critic
        
        Ensures critic is different from proposer when possible
        """
        available_models = self.llm_client.get_available_models()
        
        if not available_models:
            return None
        
        # Try to use configured critic model
        critic_model = self.settings.critic_model
        if critic_model in available_models:
            # Ensure critic != proposer
            if proposer_model and critic_model == proposer_model:
                # Find alternative
                alternatives = [m for m in available_models if m != proposer_model]
                if alternatives:
                    return alternatives[0]
            return critic_model
        
        # Fallback: use any available model different from proposer
        if proposer_model:
            alternatives = [m for m in available_models if m != proposer_model]
            if alternatives:
                return alternatives[0]
        
        # Last resort: use first available model (self-critique)
        if self.settings.use_critique_in_single_model and available_models:
            return available_models[0]
        
        return None


# Singleton
_critique_engine = None


def get_critique_engine() -> CritiqueEngine:
    """Get or create singleton critique engine"""
    global _critique_engine
    if _critique_engine is None:
        _critique_engine = CritiqueEngine()
    return _critique_engine
