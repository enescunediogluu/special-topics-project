"""
Complete demonstration of the skill extraction and normalization pipeline.
Processes real scraped job data from an uploaded CSV file.
"""

import csv
import json
import sys
from pathlib import Path

# Import pipeline modules
from skill_extraction_pipeline import SkillExtractionPipeline
from pipeline_config_utils import (
    PipelineConfig, SkillDatabase, ResultAggregator, 
    ExportManager, QualityMetrics
)

def process_real_csv_dataset(csv_filename="postings.csv", max_rows=10):
    """Reads real job data from a CSV file and processes it through the pipeline"""
    print("=" * 80)
    print(f"LOADING REAL SCRAPED DATASET FROM: {csv_filename}")
    print("=" * 80)
    
    pipeline = SkillExtractionPipeline()
    batch_jobs = []
    
    # 1. Open and read your CSV file
    try:
        with open(csv_filename, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                if i >= max_rows:  # Limit processing so it runs quickly for your demo
                    break
                
                # Combine title and skills column text to create a rich job description text
                job_id = f"scraped_job_{i+1:03d}"
                rich_text = f"Position: {row.get('job_title', '')}.\nSkills: {row.get('job_skills', '')}"
                
                batch_jobs.append((job_id, rich_text))
                
        print(f"✓ Successfully loaded {len(batch_jobs)} jobs from CSV file for processing.\n")
        
    except FileNotFoundError:
        print(f"✗ Error: Could not find '{csv_filename}'. Make sure it is in your project folder!")
        return None

    # 2. Batch process the loaded real data
    print("=" * 80)
    print("PROCESSING BATCH THROUGH NLP PIPELINE")
    print("=" * 80)
    results = pipeline.process_batch(batch_jobs)
    
    # Display simple per-job processing metrics
    print("\nProcessing Complete! Summary:")
    print("-" * 80)
    for result in results:
        print(f"Job {result['job_id']}: Extracted {result['extraction_stats']['normalized_skills']} skills.")
        
    return results


def main():
    # Define the path to your CSV file (change name if your file is named differently)
    csv_file = "scraped_jobs.csv" 
    
    # Run the processing on the first 10 rows of your real CSV dataset
    results = process_real_csv_dataset(csv_filename=csv_file, max_rows=10)
    
    if results:
        aggregator = ResultAggregator()
        manager = ExportManager()
        
        for result in results:
            aggregator.add_result(result)
            
        summary = aggregator.get_summary()
        csv_out = manager.to_csv(results)
        
        # Save production-ready outputs to your project folder
        with open("pipeline_output.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        with open("pipeline_output.csv", "w") as f:
            f.write(csv_out)
        with open("pipeline_summary.json", "w") as f:
            json.dump(summary, f, indent=2, default=str)
            
        print("\n✓ Outputs successfully saved to pipeline_output.json and pipeline_output.csv!")

if __name__ == "__main__":
    main()