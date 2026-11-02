"""Skill Ontology graph — synonym resolution and semantic partial credit calculation."""

import json
import logging
from pathlib import Path

logger = logging.getLogger("rankwise.jd.ontology")

ONTOLOGY_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "skill_ontology.json"


class SkillOntology:
    """Manages skill taxonomy, synonym mapping, and hierarchical relations."""

    def __init__(self, json_path: Path | str | None = None):
        self.path = Path(json_path) if json_path else ONTOLOGY_PATH
        self.synonyms: dict[str, str] = {}
        self.parent_relations: dict[str, str] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.synonyms = {k.lower(): v.lower() for k, v in data.get("synonyms", {}).items()}
                    self.parent_relations = {k.lower(): v.lower() for k, v in data.get("parent_relations", {}).items()}
            except Exception as e:
                logger.error(f"Failed to load skill ontology from {self.path}: {e}")

    def normalize(self, skill: str) -> str:
        """Normalize skill string using synonym map."""
        cleaned = skill.strip().lower()
        return self.synonyms.get(cleaned, cleaned)

    def get_parent(self, skill: str) -> str | None:
        """Get immediate category parent of a skill."""
        norm = self.normalize(skill)
        return self.parent_relations.get(norm)

    def get_ancestors(self, skill: str) -> list[str]:
        """Get full ancestor chain up to top root."""
        ancestors: list[str] = []
        curr = self.normalize(skill)
        while curr in self.parent_relations:
            parent = self.parent_relations[curr]
            if parent in ancestors:  # Prevent cycles
                break
            ancestors.append(parent)
            curr = parent
        return ancestors

    def get_similarity(self, skill_a: str, skill_b: str) -> float:
        """Calculate conceptual similarity between two skills (0.0 - 1.0).

        - Exact match or synonym: 1.0
        - Direct parent/child: 0.85 (e.g. PyTorch & Deep Learning)
        - Sibling skills (sharing immediate parent): 0.75 (e.g. Flask & FastAPI, PyTorch & TensorFlow)
        - Ancestor/descendant: 0.60 (e.g. PyTorch & Machine Learning)
        - Otherwise: 0.0
        """
        norm_a = self.normalize(skill_a)
        norm_b = self.normalize(skill_b)

        if norm_a == norm_b:
            return 1.0

        parent_a = self.get_parent(norm_a)
        parent_b = self.get_parent(norm_b)

        # Direct parent/child
        if parent_a == norm_b or parent_b == norm_a:
            return 0.85

        # Siblings sharing same parent
        if parent_a and parent_b and parent_a == parent_b:
            return 0.75

        # Ancestor / Descendant
        ancestors_a = self.get_ancestors(norm_a)
        ancestors_b = self.get_ancestors(norm_b)

        if norm_b in ancestors_a or norm_a in ancestors_b:
            return 0.60

        # Shared grandparent
        if set(ancestors_a).intersection(set(ancestors_b)):
            return 0.40

        return 0.0


# Global singleton instance
ontology = SkillOntology()
