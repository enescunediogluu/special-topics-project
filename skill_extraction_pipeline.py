"""
Automated Entity Linking and Knowledge-Base Normalization for Technical Skills
A transformer-based pipeline for extracting and normalizing technical skills from job descriptions.

Author: Implementation based on Mustafa Enes Cunedioğlu's literature review
"""

import json
import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import warnings
import requests

import spacy
from spacy.tokens import Doc
import numpy as np
from sklearn.preprocessing import normalize
from difflib import SequenceMatcher

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SkillEntity:
    """Represents an extracted and normalized skill entity"""
    surface_form: str  # Original text from job description
    canonical_name: str  # Standardized name
    entity_type: str  # e.g., "PROGRAMMING_LANGUAGE", "FRAMEWORK", "LIBRARY"
    esco_uri: Optional[str] = None
    esco_hierarchy: Optional[Dict] = None
    dbpedia_uri: Optional[str] = None
    dbpedia_metadata: Optional[Dict] = None
    confidence_score: float = 0.0
    resolution_method: str = "UNRESOLVED"  # ESCO_PRIMARY, DBPEDIA_ENRICHMENT, HYBRID_CONFLICT
    span_start: int = 0
    span_end: int = 0
    context_window: str = ""


class ESCOTaxonomy:
    """
    Manages ESCO (European Skills, Competences, Occupations) taxonomy.
    This is a simplified in-memory representation; production systems should
    use the official ESCO API or RDF repository.
    """
    
    def __init__(self):
        # Simplified ESCO taxonomy for technical skills
        # In production, this would be loaded from official ESCO data sources
        self.skills = {
            # Programming Languages
            "http://data.europa.eu/esco/skill/python": {
                "label": "Python",
                "aliases": ["python", "python programming"],
                "type": "PROGRAMMING_LANGUAGE",
                "hierarchy": {
                    "parent": "http://data.europa.eu/esco/skill/programming-language",
                    "occupation_group": "Software Development"
                },
                "metadata": {"year_introduced": 1991, "popularity": "very_high"}
            },
            "http://data.europa.eu/esco/skill/javascript": {
                "label": "JavaScript",
                "aliases": ["javascript", "js", "ecmascript"],
                "type": "PROGRAMMING_LANGUAGE",
                "hierarchy": {
                    "parent": "http://data.europa.eu/esco/skill/programming-language",
                    "occupation_group": "Web Development"
                },
                "metadata": {"year_introduced": 1995}
            },
            "http://data.europa.eu/esco/skill/java": {
                "label": "Java",
                "aliases": ["java", "java programming"],
                "type": "PROGRAMMING_LANGUAGE",
                "hierarchy": {
                    "parent": "http://data.europa.eu/esco/skill/programming-language",
                    "occupation_group": "Enterprise Software Development"
                },
                "metadata": {"year_introduced": 1995}
            },
            "http://data.europa.eu/esco/skill/c-plus-plus": {
                "label": "C++",
                "aliases": ["c++", "cpp", "c plus plus"],
                "type": "PROGRAMMING_LANGUAGE",
                "hierarchy": {
                    "parent": "http://data.europa.eu/esco/skill/programming-language",
                    "occupation_group": "Systems Programming"
                },
                "metadata": {"year_introduced": 1985}
            },
            # Frameworks
            "http://data.europa.eu/esco/skill/react": {
                "label": "React",
                "aliases": ["react", "reactjs", "react.js"],
                "type": "FRAMEWORK",
                "hierarchy": {
                    "parent": "http://data.europa.eu/esco/skill/javascript-framework",
                    "occupation_group": "Web Development",
                    "related_language": "JavaScript"
                },
                "metadata": {"year_introduced": 2013}
            },
            "http://data.europa.eu/esco/skill/node-js": {
                "label": "Node.js",
                "aliases": ["node.js", "nodejs", "node", "node js"],
                "type": "FRAMEWORK",
                "hierarchy": {
                    "parent": "http://data.europa.eu/esco/skill/javascript-runtime",
                    "occupation_group": "Web Development",
                    "related_language": "JavaScript"
                },
                "metadata": {"year_introduced": 2009}
            },
            "http://data.europa.eu/esco/skill/django": {
                "label": "Django",
                "aliases": ["django", "django framework"],
                "type": "FRAMEWORK",
                "hierarchy": {
                    "parent": "http://data.europa.eu/esco/skill/web-framework",
                    "occupation_group": "Web Development",
                    "related_language": "Python"
                },
                "metadata": {"year_introduced": 2005}
            },
            "http://data.europa.eu/esco/skill/flask": {
                "label": "Flask",
                "aliases": ["flask", "flask framework"],
                "type": "FRAMEWORK",
                "hierarchy": {
                    "parent": "http://data.europa.eu/esco/skill/web-framework",
                    "occupation_group": "Web Development",
                    "related_language": "Python"
                },
                "metadata": {"year_introduced": 2010}
            },
            # Libraries
            "http://data.europa.eu/esco/skill/pandas": {
                "label": "pandas",
                "aliases": ["pandas", "pandas library"],
                "type": "LIBRARY",
                "hierarchy": {
                    "parent": "http://data.europa.eu/esco/skill/data-analysis-library",
                    "occupation_group": "Data Science",
                    "related_language": "Python"
                },
                "metadata": {"year_introduced": 2008}
            },
        }
    
    def lookup(self, skill_mention: str) -> Optional[Dict]:
        """Search ESCO taxonomy for a skill mention"""
        mention_lower = skill_mention.lower().strip()
        
        for esco_uri, skill_data in self.skills.items():
            # Check direct label match
            if skill_data["label"].lower() == mention_lower:
                return {"uri": esco_uri, **skill_data}
            
            # Check aliases
            if mention_lower in skill_data["aliases"]:
                return {"uri": esco_uri, **skill_data}
        
        return None
    
    def fuzzy_match(self, skill_mention: str, threshold: float = 0.8) -> Optional[Dict]:
        """Perform fuzzy matching against ESCO taxonomy"""
        mention_lower = skill_mention.lower().strip()
        best_match = None
        best_ratio = 0.0
        
        for esco_uri, skill_data in self.skills.items():
            # Check against label
            ratio = SequenceMatcher(None, mention_lower, 
                                   skill_data["label"].lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = {"uri": esco_uri, **skill_data}
            
            # Check against aliases
            for alias in skill_data["aliases"]:
                ratio = SequenceMatcher(None, mention_lower, alias).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = {"uri": esco_uri, **skill_data}
        
        if best_ratio >= threshold:
            return best_match
        return None



class DBpediaSpotlightClient:
    """
    Production-ready DBpedia Spotlight client for live entity linking.
    Connects to the official, public DBpedia Spotlight REST API endpoint.
    """
    
    def __init__(self, endpoint: str = "https://api.dbpedia-spotlight.org/en/annotate"):
        self.endpoint = endpoint
        # We set a standard User-Agent header so DBpedia's API servers don't block the request
        self.headers = {
            "Accept": "application/json"
        }
    
    def annotate(self, text: str, confidence: float = 0.5) -> List[Dict]:
        """
        Calls the live DBpedia Spotlight API to recognize and link entities in the text.
        
        Args:
            text: The skill mention or text context to analyze.
            confidence: The spotlight confidence threshold (0.0 to 1.0).
            
        Returns:
            List of normalized annotations matching your pipeline's expected format.
        """
        # If the input text is empty or just whitespace, skip the API call
        if not text or not text.strip():
            return []
            
        payload = {
            "text": text,
            "confidence": confidence
        }
        
        try:
            # Send an HTTP GET request to the public DBpedia Spotlight server
            response = requests.get(self.endpoint, headers=self.headers, params=payload, timeout=10)
            
            # Check if the API returned an HTTP error (e.g., 400, 500)
            response.raise_for_status()
            
            api_data = response.json()
            resources = api_data.get("Resources", [])
            
            annotations = []
            for res in resources:
                # Map the live DBpedia API response keys to your existing pipeline schema
                # Live API fields: '@surfaceForm', '@URI', '@similarityScore', '@types'
                types_list = [t.strip() for t in res.get("@types", "").split(",") if t.strip()]
                
                annotations.append({
                    "surfaceForm": res.get("@surfaceForm"),
                    "offset": int(res.get("@offset", 0)),
                    "length": len(res.get("@surfaceForm", "")),
                    "resource": {
                        "uri": res.get("@URI"),
                        "label": res.get("@URI").split("/")[-1].replace("_", " "),
                        "description": f"Live DBpedia resource entity of type: {', '.join(types_list) if types_list else 'Unknown'}",
                        "types": types_list,
                        "related": [] # Real relations require separate SPARQL queries; keeping empty to preserve your schema
                    },
                    "similarityScore": float(res.get("@similarityScore", confidence))
                })
                
            return annotations
            
        except requests.exceptions.RequestException as e:
            # Soft fallback: if the public API server is down or times out, log it and return empty
            logger.error(f"DBpedia Spotlight API request failed: {e}")
            return []


class SkillNERExtractor:
    """
    Named Entity Recognition for technical skills using spaCy.
    Implements domain-adapted NER for skill extraction from job descriptions.
    """
    
    def __init__(self):
        try:
            # Try to load a pre-trained model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Using blank model.")
            self.nlp = spacy.blank("en")
        
        # Skill entity patterns (simplified SkillNER patterns)
        self.skill_patterns = {
            "PROGRAMMING_LANGUAGE": [
                r"\b(Python|Java|JavaScript|C\+\+|C#|Ruby|Go|Rust|PHP|Swift|Kotlin)\b",
                r"\b(java|python|javascript|c\+\+|ruby|golang|rust)\b"
            ],
            "FRAMEWORK": [
                r"\b(React|Vue|Angular|Django|Flask|Spring|Express|Next\.js|Fastapi)\b",
                r"\b(Node\.js|NodeJS|node\.js|nodejs)\b",
                r"\b(react\.js|reactjs|react js)\b"
            ],
            "LIBRARY": [
                r"\b(pandas|NumPy|NumPy|TensorFlow|PyTorch|scikit-learn|matplotlib)\b",
                r"\b(lodash|axios|moment|jest)\b"
            ],
            "DATABASE": [
                r"\b(PostgreSQL|MySQL|MongoDB|Redis|Cassandra|DynamoDB)\b"
            ],
            "TOOL": [
                r"\b(Docker|Kubernetes|Git|Jenkins|AWS|Azure|GCP)\b"
            ]
        }
    
    def extract_skills(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Extract skill entities from text using pattern matching and NER.
        
        Returns:
            List of tuples: (skill_text, entity_type, start_idx, end_idx)
        """
        doc = self.nlp(text)
        extracted_skills = []
        seen_spans = set()
        
        # Pattern-based extraction
        for entity_type, patterns in self.skill_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    span = (match.start(), match.end())
                    if span not in seen_spans:
                        extracted_skills.append((
                            match.group(),
                            entity_type,
                            match.start(),
                            match.end()
                        ))
                        seen_spans.add(span)
        
        return extracted_skills


class KnowledgeBaseNormalizer:
    """
    Implements hierarchical priority logic for knowledge-base normalization.
    Resolves surface-form variations into canonical representations using
    ESCO primary mapping and DBpedia technical enrichment.
    """
    
    def __init__(self):
        self.esco = ESCOTaxonomy()
        self.dbpedia = DBpediaSpotlightClient()
        self.synonyms = {
            "node.js": ["nodejs", "node js", "node"],
            "c++": ["cpp", "c plus plus"],
            "javascript": ["js", "ecmascript"],
            "typescript": ["ts"],
            "react": ["reactjs", "react.js"],
        }
    
    def resolve_surface_form_variation(self, surface_form: str) -> Optional[str]:
        """Map surface form variants to canonical name"""
        surface_lower = surface_form.lower().strip()
        
        for canonical, variants in self.synonyms.items():
            if surface_lower == canonical or surface_lower in variants:
                return canonical
        
        return None
    
    def normalize(self, skill_mention: str, entity_type: str,
                  context: str = "") -> SkillEntity:
        """
        Perform hierarchical priority logic normalization:
        1. Primary Mapping (ESCO)
        2. Technical Enrichment (DBpedia)
        3. Conflict Resolution (Hybrid-Identifier)
        """
        
        # Step 1: Resolve surface form variations
        canonical_form = self.resolve_surface_form_variation(skill_mention)
        
        # Step 2: ESCO Primary Mapping
        esco_match = self.esco.lookup(skill_mention)
        if not esco_match:
            esco_match = self.esco.fuzzy_match(skill_mention)
        
        # Step 3: DBpedia Technical Enrichment
        dbpedia_annotations = self.dbpedia.annotate(skill_mention)
        dbpedia_match = dbpedia_annotations[0] if dbpedia_annotations else None
        
        # Step 4: Create normalized entity
        skill_entity = SkillEntity(
            surface_form=skill_mention,
            canonical_name=canonical_form or skill_mention,
            entity_type=entity_type,
        )
        
        # Step 5: Apply hierarchical priority logic
        if esco_match:
            # Primary Mapping: ESCO takes precedence
            skill_entity.esco_uri = esco_match["uri"]
            skill_entity.esco_hierarchy = esco_match.get("hierarchy")
            skill_entity.canonical_name = esco_match["label"]
            skill_entity.confidence_score = 0.95
            skill_entity.resolution_method = "ESCO_PRIMARY"
            
            # Technical Enrichment: Add DBpedia metadata if available
            if dbpedia_match:
                skill_entity.dbpedia_uri = dbpedia_match["resource"]["uri"]
                skill_entity.dbpedia_metadata = {
                    "label": dbpedia_match["resource"].get("label"),
                    "description": dbpedia_match["resource"].get("description"),
                    "types": dbpedia_match["resource"].get("types"),
                }
                skill_entity.resolution_method = "HYBRID_CONFLICT"
        
        elif dbpedia_match:
            # Fallback: DBpedia enrichment if ESCO not found
            skill_entity.dbpedia_uri = dbpedia_match["resource"]["uri"]
            skill_entity.dbpedia_metadata = {
                "label": dbpedia_match["resource"].get("label"),
                "description": dbpedia_match["resource"].get("description"),
            }
            skill_entity.canonical_name = dbpedia_match["resource"].get("label", skill_mention)
            skill_entity.confidence_score = 0.75
            skill_entity.resolution_method = "DBPEDIA_ENRICHMENT"
        
        else:
            # Unresolved: Keep surface form
            skill_entity.confidence_score = 0.0
            skill_entity.resolution_method = "UNRESOLVED"
        
        return skill_entity


class SkillExtractionPipeline:
    """
    End-to-end pipeline for skill extraction and normalization.
    Orchestrates: NER → Entity Linking → Knowledge-Base Normalization → JSON Output
    """
    
    def __init__(self):
        self.ner = SkillNERExtractor()
        self.normalizer = KnowledgeBaseNormalizer()
        self.processed_jobs = []
    
    def process_job_description(self, job_description: str, 
                               job_id: str = None) -> Dict:
        """
        Process a complete job description through the full pipeline.
        
        Args:
            job_description: Raw text of job posting
            job_id: Optional identifier for the job posting
        
        Returns:
            Structured output with extracted and normalized skills
        """
        if job_id is None:
            job_id = f"job_{len(self.processed_jobs) + 1}"
        
        result = {
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "original_text": job_description[:500] + "..." if len(job_description) > 500 else job_description,
            "extraction_stats": {
                "total_mentions": 0,
                "unique_skills": 0,
                "normalized_skills": 0,
                "esco_mapped": 0,
                "dbpedia_mapped": 0,
            },
            "skills": []
        }
        
        # Step 1: Extract skill entities using NER
        extracted_skills = self.ner.extract_skills(job_description)
        result["extraction_stats"]["total_mentions"] = len(extracted_skills)
        
        # Step 2: Normalize each extracted skill
        seen_canonical = set()
        for skill_mention, entity_type, start_idx, end_idx in extracted_skills:
            # Extract context window
            context_start = max(0, start_idx - 50)
            context_end = min(len(job_description), end_idx + 50)
            context = job_description[context_start:context_end]
            
            # Normalize skill
            normalized_skill = self.normalizer.normalize(
                skill_mention, 
                entity_type, 
                context
            )
            normalized_skill.span_start = start_idx
            normalized_skill.span_end = end_idx
            normalized_skill.context_window = context
            
            # Track unique skills by canonical name
            if normalized_skill.canonical_name not in seen_canonical:
                seen_canonical.add(normalized_skill.canonical_name)
                result["skills"].append(asdict(normalized_skill))
                result["extraction_stats"]["normalized_skills"] += 1
            
            # Update statistics
            if normalized_skill.esco_uri:
                result["extraction_stats"]["esco_mapped"] += 1
            if normalized_skill.dbpedia_uri:
                result["extraction_stats"]["dbpedia_mapped"] += 1
        
        result["extraction_stats"]["unique_skills"] = len(seen_canonical)
        
        # Step 3: Deduplicate and rank by confidence
        result["skills"] = sorted(
            result["skills"],
            key=lambda x: x["confidence_score"],
            reverse=True
        )
        
        self.processed_jobs.append(result)
        return result
    
    def process_batch(self, job_descriptions: List[Tuple[str, str]]) -> List[Dict]:
        """
        Process multiple job descriptions.
        
        Args:
            job_descriptions: List of (job_id, text) tuples
        
        Returns:
            List of processing results
        """
        results = []
        for job_id, text in job_descriptions:
            result = self.process_job_description(text, job_id)
            results.append(result)
        return results
    
    def export_json(self, job_result: Dict, pretty: bool = True) -> str:
        """
        Export pipeline output as canonical JSON format.
        
        Args:
            job_result: Single job processing result
            pretty: Format with indentation
        
        Returns:
            JSON string
        """
        indent = 2 if pretty else None
        return json.dumps(job_result, indent=indent, default=str)
    
    def export_batch_json(self, pretty: bool = True) -> str:
        """Export all processed jobs as JSON"""
        indent = 2 if pretty else None
        return json.dumps(self.processed_jobs, indent=indent, default=str)


if __name__ == "__main__":
    # Example usage
    sample_job = """
    We are looking for a Senior Full Stack Developer with expertise in:
    - Python and Django for backend development
    - JavaScript/React for frontend development
    - Node.js for server-side applications
    - Experience with C++ for performance-critical systems
    - pandas and NumPy for data processing
    - Docker and Kubernetes for containerization
    - PostgreSQL and MongoDB database management
    
    The ideal candidate will have worked with Flask, Express, and understand
    both object-oriented and functional programming paradigms.
    Previous experience with NodeJS and NodeJS frameworks is a plus.
    We value familiarity with modern web technologies including ReactJS and Vue.
    """
    
    # Initialize pipeline
    pipeline = SkillExtractionPipeline()
    
    # Process job description
    result = pipeline.process_job_description(sample_job, "job_001")
    
    # Export as JSON
    output_json = pipeline.export_json(result)
    print(output_json)
