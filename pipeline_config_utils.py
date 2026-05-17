"""
Configuration, utilities, and advanced features for the skill extraction pipeline
"""

import json
import csv
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration parameters for the skill extraction pipeline"""
    
    # NER Configuration
    ner_model: str = "en_core_web_sm"
    ner_confidence_threshold: float = 0.5
    enable_fuzzy_matching: bool = True
    fuzzy_match_threshold: float = 0.8
    
    # Entity Linking Configuration
    dbpedia_confidence_threshold: float = 0.5
    use_dbpedia_enrichment: bool = True
    
    # Normalization Configuration
    use_esco_primary: bool = True
    use_dbpedia_fallback: bool = True
    resolve_surface_forms: bool = True
    
    # Output Configuration
    output_format: str = "json"  # json, csv, jsonl
    include_context_window: bool = True
    context_window_size: int = 100
    
    # Processing Configuration
    batch_size: int = 100
    max_workers: int = 4
    log_level: str = "INFO"
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> "PipelineConfig":
        """Create configuration from dictionary"""
        return cls(**{k: v for k, v in config_dict.items() 
                      if k in cls.__dataclass_fields__})


class SkillDatabase:
    """
    In-memory skill database with persistence capabilities.
    Stores extracted skills, mappings, and statistics.
    """
    
    def __init__(self):
        self.skills = {}  # canonical_name -> SkillEntity
        self.mappings = {}  # surface_form -> canonical_name
        self.statistics = {
            "total_extractions": 0,
            "unique_skills": 0,
            "esco_mapped": 0,
            "dbpedia_mapped": 0,
            "confidence_distribution": {}
        }
    
    def add_skill(self, skill_dict: Dict) -> None:
        """Add a skill entity to the database"""
        canonical = skill_dict.get("canonical_name", skill_dict.get("surface_form"))
        surface = skill_dict.get("surface_form")
        
        self.skills[canonical] = skill_dict
        self.mappings[surface] = canonical
        
        # Update statistics
        self.statistics["total_extractions"] += 1
        if canonical not in self.skills or skill_dict.get("confidence_score", 0) > \
           self.skills[canonical].get("confidence_score", 0):
            self.statistics["unique_skills"] = len(set(self.mappings.values()))
        
        if skill_dict.get("esco_uri"):
            self.statistics["esco_mapped"] += 1
        if skill_dict.get("dbpedia_uri"):
            self.statistics["dbpedia_mapped"] += 1
    
    def get_skill(self, surface_form: str) -> Optional[Dict]:
        """Retrieve skill by surface form"""
        canonical = self.mappings.get(surface_form)
        return self.skills.get(canonical) if canonical else None
    
    def get_all_skills(self) -> List[Dict]:
        """Get all unique skills"""
        return list(self.skills.values())
    
    def export_csv(self, filepath: str) -> None:
        """Export skills to CSV format"""
        skills = self.get_all_skills()
        if not skills:
            logger.warning("No skills to export")
            return
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=skills[0].keys())
            writer.writeheader()
            writer.writerows(skills)
        
        logger.info(f"Exported {len(skills)} skills to {filepath}")
    
    def export_json(self, filepath: str) -> None:
        """Export skills to JSON format"""
        skills = self.get_all_skills()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(skills, f, indent=2, default=str)
        logger.info(f"Exported {len(skills)} skills to {filepath}")
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        return {
            **self.statistics,
            "unique_canonical_names": len(self.skills),
            "surface_form_variants": len(self.mappings),
            "mapping_rate": len(self.skills) / max(1, len(self.mappings))
        }


class ResultAggregator:
    """
    Aggregates results from batch processing and provides statistical summaries.
    """
    
    def __init__(self):
        self.results = []
        self.skill_frequency = {}
        self.entity_type_distribution = {}
    
    def add_result(self, job_result: Dict) -> None:
        """Add a job processing result"""
        self.results.append(job_result)
        
        # Update aggregated statistics
        for skill in job_result.get("skills", []):
            canonical = skill.get("canonical_name")
            entity_type = skill.get("entity_type")
            
            self.skill_frequency[canonical] = self.skill_frequency.get(canonical, 0) + 1
            self.entity_type_distribution[entity_type] = \
                self.entity_type_distribution.get(entity_type, 0) + 1
    
    def get_top_skills(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Get most frequently extracted skills"""
        return sorted(self.skill_frequency.items(), 
                     key=lambda x: x[1], reverse=True)[:limit]
    
    def get_entity_type_stats(self) -> Dict[str, int]:
        """Get distribution of entity types"""
        return dict(sorted(self.entity_type_distribution.items(), 
                          key=lambda x: x[1], reverse=True))
    
    def get_summary(self) -> Dict:
        """Get comprehensive summary statistics"""
        total_jobs = len(self.results)
        total_skills = sum(len(r.get("skills", [])) for r in self.results)
        total_mentions = sum(r.get("extraction_stats", {}).get("total_mentions", 0) 
                            for r in self.results)
        
        return {
            "jobs_processed": total_jobs,
            "total_skill_mentions": total_mentions,
            "total_normalized_skills": total_skills,
            "average_skills_per_job": total_skills / max(1, total_jobs),
            "unique_skills": len(self.skill_frequency),
            "top_skills": self.get_top_skills(10),
            "entity_type_distribution": self.get_entity_type_stats(),
            "esco_coverage": sum(r.get("extraction_stats", {}).get("esco_mapped", 0) 
                               for r in self.results) / max(1, total_skills) * 100,
            "dbpedia_coverage": sum(r.get("extraction_stats", {}).get("dbpedia_mapped", 0) 
                                   for r in self.results) / max(1, total_skills) * 100
        }


class ExportManager:
    """
    Manages export of pipeline results in multiple formats.
    """
    
    @staticmethod
    def to_jsonl(results: List[Dict]) -> str:
        """Export results as JSON Lines (one object per line)"""
        lines = [json.dumps(r, default=str) for r in results]
        return '\n'.join(lines)
    
    @staticmethod
    def to_csv(results: List[Dict], filepath: str = None) -> Optional[str]:
        """Export flattened results to CSV"""
        flattened = []
        
        for result in results:
            job_id = result.get("job_id")
            for skill in result.get("skills", []):
                flattened.append({
                    "job_id": job_id,
                    "surface_form": skill.get("surface_form"),
                    "canonical_name": skill.get("canonical_name"),
                    "entity_type": skill.get("entity_type"),
                    "confidence_score": skill.get("confidence_score"),
                    "esco_uri": skill.get("esco_uri"),
                    "dbpedia_uri": skill.get("dbpedia_uri"),
                    "resolution_method": skill.get("resolution_method")
                })
        
        if filepath:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if flattened:
                    writer = csv.DictWriter(f, fieldnames=flattened[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened)
            return None
        else:
            output = []
            if flattened:
                keys = flattened[0].keys()
                output.append(','.join(keys))
                for row in flattened:
                    output.append(','.join(str(row.get(k, "")) for k in keys))
            return '\n'.join(output)
    
    @staticmethod
    def to_database_schema(results: List[Dict]) -> Dict:
        """
        Generate database schema and insertion statements for SQL integration.
        Perfectly matches the 3-table relational design specified in the project report.
        """
        schema = {
            "tables": {
                "Jobs": {
                    "columns": {
                        "job_id": "VARCHAR(255) PRIMARY KEY",
                        "timestamp": "DATETIME",
                        "original_text": "TEXT"
                    }
                },
                "Skills": {
                    "columns": {
                        "canonical_name": "VARCHAR(255) PRIMARY KEY",
                        "entity_type": "VARCHAR(50)",
                        "esco_uri": "VARCHAR(500)",
                        "dbpedia_uri": "VARCHAR(500)"
                    }
                },
                "Job_Skills": {
                    "columns": {
                        "job_id": "VARCHAR(255) REFERENCES Jobs(job_id)",
                        "canonical_name": "VARCHAR(255) REFERENCES Skills(canonical_name)",
                        "surface_form": "VARCHAR(255)",
                        "confidence_score": "FLOAT",
                        "resolution_method": "VARCHAR(50)"
                    },
                    "primary_key": ["job_id", "canonical_name"]
                }
            },
            "insert_statements": {
                "Jobs": [],
                "Skills": [],
                "Job_Skills": []
            }
        }
        
        seen_skills = set()
        for result in results:
            job_id = result.get("job_id")
            schema["insert_statements"]["Jobs"].append(
                f"INSERT INTO Jobs (job_id, timestamp, original_text) VALUES ('{job_id}', '{result.get('timestamp')}', '...');"
            )
            
            for skill in result.get("skills", []):
                canonical = skill.get("canonical_name")
                
                # Populate global Skills table uniquely
                if canonical not in seen_skills:
                    seen_skills.add(canonical)
                    schema["insert_statements"]["Skills"].append({
                        "canonical_name": canonical,
                        "entity_type": skill.get("entity_type"),
                        "esco_uri": skill.get("esco_uri"),
                        "dbpedia_uri": skill.get("dbpedia_uri")
                    })
                
                # Populate associative bridge table
                schema["insert_statements"]["Job_Skills"].append({
                    "job_id": job_id,
                    "canonical_name": canonical,
                    "surface_form": skill.get("surface_form"),
                    "confidence_score": skill.get("confidence_score"),
                    "resolution_method": skill.get("resolution_method")
                })
        
        return schema


class QualityMetrics:
    """
    Compute quality metrics for extraction and normalization results.
    """
    
    @staticmethod
    def compute_coverage(results: List[Dict]) -> Dict[str, float]:
        """
        Compute knowledge base coverage metrics.
        Shows percentage of skills mapped to ESCO and DBpedia.
        """
        total_skills = 0
        esco_mapped = 0
        dbpedia_mapped = 0
        hybrid_mapped = 0
        unresolved = 0
        
        for result in results:
            for skill in result.get("skills", []):
                total_skills += 1
                esco = skill.get("esco_uri") is not None
                dbpedia = skill.get("dbpedia_uri") is not None
                
                if esco and dbpedia:
                    hybrid_mapped += 1
                elif esco:
                    esco_mapped += 1
                elif dbpedia:
                    dbpedia_mapped += 1
                else:
                    unresolved += 1
        
        return {
            "total_skills": total_skills,
            "esco_coverage": esco_mapped / max(1, total_skills) * 100,
            "dbpedia_coverage": dbpedia_mapped / max(1, total_skills) * 100,
            "hybrid_coverage": hybrid_mapped / max(1, total_skills) * 100,
            "unresolved_rate": unresolved / max(1, total_skills) * 100
        }
    
    @staticmethod
    def compute_confidence_stats(results: List[Dict]) -> Dict:
        """Compute confidence score statistics"""
        scores = []
        
        for result in results:
            for skill in result.get("skills", []):
                scores.append(skill.get("confidence_score", 0))
        
        if not scores:
            return {"count": 0}
        
        import statistics
        return {
            "count": len(scores),
            "mean": statistics.mean(scores),
            "median": statistics.median(scores),
            "min": min(scores),
            "max": max(scores),
            "stdev": statistics.stdev(scores) if len(scores) > 1 else 0
        }
    
    @staticmethod
    def deduplicate_analysis(results: List[Dict]) -> Dict:
        """
        Analyze deduplication effectiveness.
        Shows how many surface forms map to the same canonical skill.
        """
        canonical_to_surfaces = {}
        
        for result in results:
            for skill in result.get("skills", []):
                canonical = skill.get("canonical_name")
                surface = skill.get("surface_form")
                
                if canonical not in canonical_to_surfaces:
                    canonical_to_surfaces[canonical] = set()
                canonical_to_surfaces[canonical].add(surface)
        
        # Compute statistics
        total_unique = len(canonical_to_surfaces)
        total_variants = sum(len(surfaces) for surfaces in canonical_to_surfaces.values())
        avg_variants = total_variants / max(1, total_unique)
        
        # Find most ambiguous skills
        most_ambiguous = sorted(
            [(k, len(v)) for k, v in canonical_to_surfaces.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "total_unique_skills": total_unique,
            "total_surface_variants": total_variants,
            "average_variants_per_skill": avg_variants,
            "most_ambiguous_skills": most_ambiguous
        }
