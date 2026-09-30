"""
Consensus Engine - Multi-LLM claim clustering and confidence scoring
"""
from typing import List, Dict, Any
from sklearn.cluster import DBSCAN
import numpy as np
from app.workflows.state import Finding, ClaimCluster
from app.services.embedding import get_embedding_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConsensusEngine:
    """
    Builds consensus from multi-LLM findings using DBSCAN clustering
    and multi-dimensional confidence scoring
    """
    
    def __init__(self, eps: float = 0.12, min_samples: int = 2):
        """
        Args:
            eps: DBSCAN epsilon for semantic similarity threshold
            min_samples: Minimum samples per cluster
        """
        self.eps = eps
        self.min_samples = min_samples
        self.embedding_service = get_embedding_service()
    
    async def build_consensus(
        self,
        llm_outputs: Dict[str, List[Finding]],
        element_content: str,
        regulation_texts: List[str]
    ) -> tuple[List[ClaimCluster], List[Finding], List[Finding]]:
        """
        Build consensus from multi-LLM outputs
        
        Returns:
            (claim_clusters, high_confidence_findings, medium_confidence_findings)
        """
        from app.config import get_settings
        settings = get_settings()
        
        # Extract all findings
        all_findings = []
        for model_name, findings in llm_outputs.items():
            for finding in findings:
                finding['model_name'] = model_name
                all_findings.append(finding)
        
        if not all_findings:
            return [], [], []
        
        # Generate embeddings for each claim
        logger.info(f"Generating embeddings for {len(all_findings)} findings")
        claim_texts = [f"{f['description']} {f['evidence']}" for f in all_findings]
        embeddings = await self.embedding_service.generate_embeddings_batch(
            claim_texts,
            task_type="SEMANTIC_SIMILARITY"
        )
        
        # Cluster using DBSCAN
        clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric='cosine')
        labels = clustering.fit_predict(embeddings)
        
        # Build clusters
        clusters = self._build_clusters(all_findings, embeddings, labels, llm_outputs)
        
        # Score each cluster
        scored_clusters = []
        # Use configurable thresholds from settings
        high_threshold = settings.high_confidence_threshold
        medium_threshold = settings.medium_confidence_threshold
        
        for cluster in clusters:
            confidence = await self._calculate_confidence_score(
                cluster,
                element_content,
                regulation_texts,
                embeddings,
                llm_outputs
            )
            cluster['confidence_score'] = confidence
            cluster['is_high_confidence'] = confidence >= high_threshold
            scored_clusters.append(cluster)
        
        # Filter by confidence
        high_confidence = [
            c['representative_finding']
            for c in scored_clusters
            if c['confidence_score'] >= high_threshold
        ]
        medium_confidence = [
            c['representative_finding']
            for c in scored_clusters
            if medium_threshold <= c['confidence_score'] < high_threshold
        ]
        
        logger.info(
            f"Consensus: {len(high_confidence)} high, {len(medium_confidence)} medium confidence findings "
            f"(thresholds: {high_threshold}/{medium_threshold})"
        )
        
        return scored_clusters, high_confidence, medium_confidence
    
    def _build_clusters(
        self,
        findings: List[Finding],
        embeddings: List[List[float]],
        labels: np.ndarray,
        llm_outputs: Dict[str, List[Finding]]
    ) -> List[ClaimCluster]:
        """Build ClaimCluster objects from DBSCAN results"""
        clusters = []
        unique_labels = set(labels)
        
        for label in unique_labels:
            if label == -1:  # Noise points
                continue
            
            # Get findings in this cluster
            cluster_indices = np.where(labels == label)[0]
            cluster_findings = [findings[i] for i in cluster_indices]
            
            # Count model agreement
            models_in_cluster = set(f['model_name'] for f in cluster_findings)
            # Use number of models that provided outputs instead of hardcoded 3.0
            total_active_models = len(llm_outputs) if llm_outputs else 1
            model_agreement = len(models_in_cluster) / float(total_active_models)
            
            # Select representative finding (highest semantic centrality)
            cluster_embeddings = [embeddings[i] for i in cluster_indices]
            centroid = np.mean(cluster_embeddings, axis=0)
            similarities = [
                self._cosine_similarity(centroid, emb)
                for emb in cluster_embeddings
            ]
            representative_idx = cluster_indices[np.argmax(similarities)]
            
            cluster = ClaimCluster(
                cluster_id=f"cluster_{label}",
                findings=cluster_findings,
                representative_finding=findings[representative_idx],
                model_agreement=model_agreement,
                confidence_score=0.0,  # Will be calculated
                is_high_confidence=False
            )
            clusters.append(cluster)
        
        return clusters
    
    async def _calculate_confidence_score(
        self,
        cluster: ClaimCluster,
        element_content: str,
        regulation_texts: List[str],
        all_embeddings: List[List[float]],
        llm_outputs: Dict[str, List[Finding]]
    ) -> float:
        """
        Calculate multi-dimensional confidence score with configurable method
        
        Supports three methods:
        - agreement: Based purely on model agreement
        - confidence: Based on individual model confidence scores
        - hybrid: Weighted combination (default)
        """
        from app.config import get_settings
        settings = get_settings()
        
        # 1. Agreement score: How many models agree
        agreement_score = cluster['model_agreement']
        
        # 2. Individual model confidence: Average confidence from models
        individual_confidence = self._get_average_model_confidence(cluster['findings'])
        
        # 3. Grounding score: Is claim verified in source?
        grounding_score = self._calculate_grounding_score(
            cluster['representative_finding'],
            element_content
        )
        
        # 4. Regulation strength: Citation quality
        regulation_strength = self._calculate_regulation_strength(
            cluster['representative_finding'],
            regulation_texts
        )
        
        # 5. Semantic consistency: Embedding similarity within cluster
        semantic_consistency = self._calculate_semantic_consistency(
            cluster['findings'],
            all_embeddings
        )
        
        # Apply consensus method
        if settings.consensus_method == "agreement":
            # Pure agreement-based scoring
            confidence = (
                0.70 * agreement_score +
                0.15 * grounding_score +
                0.10 * regulation_strength +
                0.05 * semantic_consistency
            )
        elif settings.consensus_method == "confidence":
            # Individual confidence-based scoring
            confidence = (
                0.60 * individual_confidence +
                0.20 * grounding_score +
                0.10 * regulation_strength +
                0.10 * semantic_consistency
            )
        else:  # hybrid (default)
            # Balanced approach
            confidence = (
                0.35 * agreement_score +
                0.25 * individual_confidence +
                0.25 * grounding_score +
                0.10 * regulation_strength +
                0.05 * semantic_consistency
            )
        
        return min(1.0, max(0.0, confidence))
    
    def _get_average_model_confidence(self, findings: List[Finding]) -> float:
        """Extract and average individual model confidence scores"""
        confidences = []
        for finding in findings:
            # Models may provide their own confidence in meta or as a field
            model_conf = finding.get('confidence', finding.get('meta', {}).get('confidence'))
            if model_conf is not None:
                try:
                    confidences.append(float(model_conf))
                except (ValueError, TypeError):
                    pass
        
        if not confidences:
            # If no model provided confidence, assume moderate
            return 0.75
        
        return sum(confidences) / len(confidences)

    
    def _calculate_grounding_score(self, finding: Finding, element_content: str) -> float:
        """Check if finding is grounded in source document"""
        evidence = finding.get('evidence', '').lower()
        content = element_content.lower()
        
        if not evidence:
            return 0.0
        
        # Exact match
        if evidence in content:
            return 1.0
        
        # Fuzzy match (at least 80% of words present)
        evidence_words = set(evidence.split())
        content_words = set(content.split())
        overlap = len(evidence_words & content_words) / len(evidence_words) if evidence_words else 0
        
        return overlap
    
    def _calculate_regulation_strength(
        self,
        finding: Finding,
        regulation_texts: List[str]
    ) -> float:
        """Assess quality of regulation citation"""
        reg_ref = finding.get('regulation_ref', '').lower()
        
        if not reg_ref:
            return 0.0
        
        # Check if cited regulation exists in retrieved regulations
        for reg_text in regulation_texts:
            if reg_ref in reg_text.lower():
                return 1.0
        
        # Has a regulation reference format but not found
        if any(marker in reg_ref for marker in ['§', 'rule', '.']):
            return 0.5
        
        return 0.0
    
    def _calculate_semantic_consistency(
        self,
        findings: List[Finding],
        all_embeddings: List[List[float]]
    ) -> float:
        """Calculate average pairwise similarity in cluster"""
        if len(findings) < 2:
            return 1.0
        
        # This is simplified - in full implementation would get cluster embeddings
        # For now, return high score if multiple models agree
        return min(1.0, len(findings) / 3.0)
    
    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# Singleton
_consensus_engine = None

async def get_consensus_engine() -> ConsensusEngine:
    """Get or create singleton consensus engine"""
    global _consensus_engine
    if _consensus_engine is None:
        # Lower min_samples to 1 to handle 2-model scenario
        _consensus_engine = ConsensusEngine(eps=0.12, min_samples=1)
    return _consensus_engine
