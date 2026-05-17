"""
Complete demonstration of the skill extraction and normalization pipeline.
Shows end-to-end processing with examples, output formats, and analysis.
"""

import json
import sys
from pathlib import Path

# Import pipeline modules
from skill_extraction_pipeline import SkillExtractionPipeline
from pipeline_config_utils import (
    PipelineConfig, SkillDatabase, ResultAggregator, 
    ExportManager, QualityMetrics
)


# ============================================================================
# SAMPLE JOB DESCRIPTIONS FOR DEMONSTRATION
# ============================================================================

SAMPLE_JOBS = [
    {
        "job_id": "job_001",
        "title": "Senior Full Stack Developer",
        "text": """
        Position: Senior Full Stack Developer
        
        We are seeking a talented Full Stack Developer with expertise in:
        
        Backend Technologies:
        - Python programming language with Django and Flask frameworks
        - Java for enterprise-level applications
        - C++ for performance-critical systems
        - Node.js and Express.js for server-side JavaScript
        - PostgreSQL and MongoDB database management
        
        Frontend Technologies:
        - JavaScript and modern frameworks (React, Vue.js)
        - ReactJS and React.js experience required
        - CSS, HTML5, and responsive web design
        
        DevOps & Tools:
        - Docker containerization and Kubernetes orchestration
        - AWS cloud services and Azure
        - Git version control
        - CI/CD pipelines with Jenkins
        
        Data Processing:
        - pandas library for data analysis
        - NumPy for numerical computing
        - TensorFlow or PyTorch for machine learning
        
        Required Skills:
        You should be comfortable working with Python, JavaScript, and Java.
        Experience with Node.js applications and React development is essential.
        Knowledge of both C++ and modern web frameworks would be advantageous.
        """
    },
    {
        "job_id": "job_002",
        "title": "Data Science Engineer",
        "text": """
        We are looking for a Data Science Engineer with strong background in:
        
        Core Skills:
        - Python programming language (essential)
        - R for statistical analysis
        - Machine learning with TensorFlow and PyTorch
        - Data manipulation using pandas and NumPy
        - SQL for database queries
        
        Big Data:
        - Apache Spark for large-scale data processing
        - Hadoop ecosystem
        - Scala programming language
        
        Data Visualization:
        - Matplotlib and Seaborn libraries
        - Tableau or Power BI
        - D3.js for interactive visualizations
        
        Cloud & DevOps:
        - AWS services (S3, EC2, SageMaker)
        - Docker and containerization
        - Apache Airflow for workflow orchestration
        
        Version Control:
        - Git and GitHub
        - Experience with GitLab or Bitbucket
        
        Plus, familiarity with Kubernetes and Apache Kafka is a bonus.
        """
    },
    {
        "job_id": "job_003",
        "title": "Frontend Engineer - React",
        "text": """
        Frontend Engineer - React.js Specialist
        
        About the Role:
        We're seeking a Frontend Engineer who is passionate about React development.
        
        Required Technologies:
        - JavaScript programming language (expert level)
        - React and React.js for building user interfaces
        - TypeScript for type-safe JavaScript
        - HTML5 and CSS3
        - Node.js and npm for development tooling
        - npm and Yarn package managers
        
        State Management:
        - Redux or MobX
        - Context API
        
        Testing:
        - Jest testing framework
        - React Testing Library
        
        Build Tools:
        - Webpack for module bundling
        - Babel transpiler
        - Gulp or Grunt task runners
        
        Modern Web Technologies:
        - Vue.js experience is a plus (even though React is our focus)
        - Next.js for server-side React applications
        - GraphQL for API queries
        
        Version Control:
        - Git version control system
        
        Bonus Skills:
        - GraphQL Apollo client
        - Styled Components or CSS-in-JS solutions
        - Experience with JavaScript frameworks beyond React
        """
    }
]


def demo_single_job_processing():
    """Demonstrate processing a single job description"""
    print("=" * 80)
    print("DEMO 1: Single Job Description Processing")
    print("=" * 80)
    
    pipeline = SkillExtractionPipeline()
    job = SAMPLE_JOBS[0]
    
    print(f"\nJob Title: {job['title']}")
    print(f"Job ID: {job['job_id']}")
    print(f"Text Preview: {job['text'][:200]}...\n")
    
    # Process the job
    result = pipeline.process_job_description(job['text'], job['job_id'])
    
    # Display results
    print(f"Extraction Statistics:")
    print(f"  Total Mentions: {result['extraction_stats']['total_mentions']}")
    print(f"  Unique Skills: {result['extraction_stats']['unique_skills']}")
    print(f"  Normalized: {result['extraction_stats']['normalized_skills']}")
    print(f"  ESCO Mapped: {result['extraction_stats']['esco_mapped']}")
    print(f"  DBpedia Mapped: {result['extraction_stats']['dbpedia_mapped']}")
    
    print(f"\nExtracted Skills:")
    print("-" * 80)
    for i, skill in enumerate(result['skills'], 1):
        print(f"\n{i}. {skill['surface_form']}")
        print(f"   Canonical Name: {skill['canonical_name']}")
        print(f"   Type: {skill['entity_type']}")
        print(f"   Confidence: {skill['confidence_score']:.2f}")
        print(f"   Resolution: {skill['resolution_method']}")
        if skill['esco_uri']:
            print(f"   ESCO: {skill['esco_uri']}")
        if skill['dbpedia_uri']:
            print(f"   DBpedia: {skill['dbpedia_uri']}")
    
    return result


def demo_batch_processing():
    """Demonstrate batch processing of multiple jobs"""
    print("\n" + "=" * 80)
    print("DEMO 2: Batch Processing Multiple Job Descriptions")
    print("=" * 80)
    
    pipeline = SkillExtractionPipeline()
    
    # Prepare batch
    batch_jobs = [(job['job_id'], job['text']) for job in SAMPLE_JOBS]
    
    print(f"\nProcessing {len(batch_jobs)} job descriptions...\n")
    
    # Process batch
    results = pipeline.process_batch(batch_jobs)
    
    # Display summary
    print(f"Batch Processing Complete:")
    print(f"  Jobs Processed: {len(results)}")
    print(f"  Total Skills Extracted: {sum(len(r['skills']) for r in results)}")
    print(f"  Total Mentions: {sum(r['extraction_stats']['total_mentions'] for r in results)}")
    
    print("\nPer-Job Summary:")
    print("-" * 80)
    for result in results:
        print(f"\nJob {result['job_id']}:")
        print(f"  Skills Extracted: {result['extraction_stats']['normalized_skills']}")
        print(f"  Coverage: ESCO={result['extraction_stats']['esco_mapped']}, "
              f"DBpedia={result['extraction_stats']['dbpedia_mapped']}")
    
    return results


def demo_export_formats(results):
    """Demonstrate various export formats"""
    print("\n" + "=" * 80)
    print("DEMO 3: Export Formats")
    print("=" * 80)
    
    manager = ExportManager()
    
    # JSON Export
    print("\n1. JSON Format (Pretty-printed):")
    print("-" * 80)
    json_output = json.dumps(results[0], indent=2, default=str)
    print(json_output[:500] + "...\n")
    
    # JSONL Export
    print("2. JSON Lines Format (streaming):")
    print("-" * 80)
    jsonl_output = manager.to_jsonl(results)
    print(jsonl_output.split('\n')[0] + "\n...")
    
    # CSV Export
    print("\n3. CSV Format (flattened):")
    print("-" * 80)
    csv_output = manager.to_csv(results)
    csv_lines = csv_output.split('\n')
    print(csv_lines[0])  # Header
    for line in csv_lines[1:4]:  # First few rows
        print(line)
    print(f"... ({len(csv_lines)-1} total rows)\n")
    
    # Database Schema
    print("4. Database Schema for SQL Integration:")
    print("-" * 80)
    schema = manager.to_database_schema(results)
    print("Tables:")
    for table_name, table_info in schema['tables'].items():
        print(f"  - {table_name}")
        print(f"    Columns: {list(table_info['columns'].keys())}")
    
    print(f"\nSample INSERT statements (first 2):")
    for stmt in schema['insert_statements']['skills'][:2]:
        print(f"  INSERT INTO extracted_skills VALUES ...")
        for k, v in stmt.items():
            print(f"    {k}: {v}")
    
    return json_output, csv_output


def demo_analytics_and_metrics(results):
    """Demonstrate analytics and quality metrics"""
    print("\n" + "=" * 80)
    print("DEMO 4: Analytics and Quality Metrics")
    print("=" * 80)
    
    aggregator = ResultAggregator()
    for result in results:
        aggregator.add_result(result)
    
    # Summary Statistics
    print("\nSummary Statistics:")
    print("-" * 80)
    summary = aggregator.get_summary()
    print(f"Jobs Processed: {summary['jobs_processed']}")
    print(f"Total Skill Mentions: {summary['total_skill_mentions']}")
    print(f"Total Normalized Skills: {summary['total_normalized_skills']}")
    print(f"Average Skills per Job: {summary['average_skills_per_job']:.2f}")
    print(f"Unique Skills Identified: {summary['unique_skills']}")
    print(f"ESCO Coverage: {summary['esco_coverage']:.1f}%")
    print(f"DBpedia Coverage: {summary['dbpedia_coverage']:.1f}%")
    
    # Top Skills
    print(f"\nTop 10 Most Frequently Mentioned Skills:")
    print("-" * 80)
    for i, (skill, count) in enumerate(summary['top_skills'], 1):
        print(f"{i:2d}. {skill:30s} - {count} mentions")
    
    # Entity Type Distribution
    print(f"\nEntity Type Distribution:")
    print("-" * 80)
    for entity_type, count in summary['entity_type_distribution'].items():
        print(f"  {entity_type:25s}: {count:3d} ({count/summary['total_normalized_skills']*100:5.1f}%)")
    
    # Knowledge Base Coverage
    print(f"\nKnowledge Base Coverage Analysis:")
    print("-" * 80)
    coverage = QualityMetrics.compute_coverage(results)
    print(f"Total Skills Analyzed: {coverage['total_skills']}")
    print(f"ESCO Mapped: {coverage['esco_coverage']:6.1f}%")
    print(f"DBpedia Mapped: {coverage['dbpedia_coverage']:6.1f}%")
    print(f"Hybrid (Both ESCO & DBpedia): {coverage['hybrid_coverage']:6.1f}%")
    print(f"Unresolved: {coverage['unresolved_rate']:6.1f}%")
    
    # Confidence Statistics
    print(f"\nConfidence Score Statistics:")
    print("-" * 80)
    conf_stats = QualityMetrics.compute_confidence_stats(results)
    if conf_stats['count'] > 0:
        print(f"Count: {conf_stats['count']}")
        print(f"Mean: {conf_stats['mean']:.3f}")
        print(f"Median: {conf_stats['median']:.3f}")
        print(f"Min: {conf_stats['min']:.3f}")
        print(f"Max: {conf_stats['max']:.3f}")
        if 'stdev' in conf_stats:
            print(f"Std Dev: {conf_stats['stdev']:.3f}")
    
    # Deduplication Analysis
    print(f"\nSurface Form Deduplication Analysis:")
    print("-" * 80)
    dedup = QualityMetrics.deduplicate_analysis(results)
    print(f"Unique Canonical Skills: {dedup['total_unique_skills']}")
    print(f"Total Surface Form Variants: {dedup['total_surface_variants']}")
    print(f"Avg Variants per Skill: {dedup['average_variants_per_skill']:.2f}")
    
    print(f"\nMost Ambiguous Skills (most variants):")
    for skill, variant_count in dedup['most_ambiguous_skills'][:5]:
        print(f"  {skill:30s} - {variant_count} variants")
    
    return summary


def demo_hierarchical_priority_logic():
    """Demonstrate the hierarchical priority logic for conflict resolution"""
    print("\n" + "=" * 80)
    print("DEMO 5: Hierarchical Priority Logic for Conflict Resolution")
    print("=" * 80)
    
    print("""
The pipeline implements a three-tier hierarchical priority logic for knowledge-base normalization:

1. PRIMARY MAPPING (ESCO - Highest Priority)
   - When a skill mention matches ESCO taxonomy
   - Ensures labor-market standard classification
   - Example: "Python" → ESCO URI with occupation hierarchy
   - Confidence: 0.95

2. TECHNICAL ENRICHMENT (DBpedia)
   - If ESCO match exists, DBpedia adds granular metadata
   - Links to version info, related projects, descriptions
   - Example: "Node.js" → Links to JavaScript runtime details
   - Resolution Method: HYBRID_CONFLICT

3. FALLBACK ENRICHMENT (DBpedia Primary)
   - If ESCO has no match, use DBpedia as primary source
   - Captures emerging/specialized technologies
   - Example: New frameworks not yet in ESCO
   - Confidence: 0.75

4. UNRESOLVED
   - Surface form cannot be mapped to any KB
   - Kept as-is for manual review
   - Confidence: 0.0
    """)
    
    print("Example Resolution Processes:")
    print("-" * 80)
    
    test_cases = [
        ("Python", "ESCO primary → PROGRAMMING_LANGUAGE"),
        ("Node.js", "ESCO primary + DBpedia enrichment → framework metadata"),
        ("NodeJS", "Surface form variation → normalized to Node.js"),
        ("C++", "ESCO primary + alias resolution → CPP → C++"),
        ("ReactJS", "ESCO primary + React.js variant resolution"),
    ]
    
    for surface_form, expected in test_cases:
        print(f"\nInput: '{surface_form}'")
        print(f"Resolution: {expected}")


def demo_skill_database():
    """Demonstrate skill database functionality"""
    print("\n" + "=" * 80)
    print("DEMO 6: Skill Database Management")
    print("=" * 80)
    
    pipeline = SkillExtractionPipeline()
    batch_jobs = [(job['job_id'], job['text']) for job in SAMPLE_JOBS]
    results = pipeline.process_batch(batch_jobs)
    
    # Create and populate skill database
    db = SkillDatabase()
    for result in results:
        for skill in result['skills']:
            db.add_skill(skill)
    
    # Get database stats
    stats = db.get_statistics()
    
    print(f"\nSkill Database Statistics:")
    print("-" * 80)
    print(f"Total Extractions: {stats['total_extractions']}")
    print(f"Unique Canonical Names: {stats['unique_canonical_names']}")
    print(f"Surface Form Variants: {stats['surface_form_variants']}")
    print(f"ESCO Mapped: {stats['esco_mapped']}")
    print(f"DBpedia Mapped: {stats['dbpedia_mapped']}")
    print(f"Mapping Rate: {stats['mapping_rate']:.2f}")
    
    print(f"\nAll Unique Skills in Database:")
    print("-" * 80)
    all_skills = db.get_all_skills()
    for i, skill in enumerate(sorted(all_skills, 
                                     key=lambda x: x.get('canonical_name')), 1):
        print(f"{i:2d}. {skill['canonical_name']:25s} "
              f"({skill['entity_type']:20s}) "
              f"[Confidence: {skill['confidence_score']:.2f}]")


def main():
    """Run all demonstrations"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "AUTOMATED ENTITY LINKING AND KNOWLEDGE-BASE NORMALIZATION".center(78) + "║")
    print("║" + "for Technical Skills - Complete Pipeline Demonstration".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝\n")
    
    try:
        # Run demonstrations
        result1 = demo_single_job_processing()
        results = demo_batch_processing()
        json_out, csv_out = demo_export_formats(results)
        summary = demo_analytics_and_metrics(results)
        demo_hierarchical_priority_logic()
        demo_skill_database()
        
        # Save outputs
        print("\n" + "=" * 80)
        print("Saving Outputs")
        print("=" * 80)
        
        output_dir = Path(".")
        
        # Save JSON
        with open(output_dir / "pipeline_output.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print("✓ Saved pipeline_output.json")
        
        # Save CSV
        with open(output_dir / "pipeline_output.csv", "w") as f:
            f.write(csv_out)
        print("✓ Saved pipeline_output.csv")
        
        # Save summary
        with open(output_dir / "pipeline_summary.json", "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print("✓ Saved pipeline_summary.json")
        
        print("\n" + "=" * 80)
        print("✓ All demonstrations completed successfully!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
