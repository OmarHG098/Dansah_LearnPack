import pandas as pd
import yaml

# Category order as defined in functions.py
CATEGORIES = [
    "OnlinePlatform",
    "MentorsTeachers",
    "Price",
    "CareerSupport",
    "ContentSyllabus",
    "Job Guarantee",
    "FullStack",
    "Cybersecurity",
    "DataScience",
    "AppliedAI",
    "Outcomes",
    "Scholarships",
    "Rigobot",
    "LearnPack"
]

def transform_csv_to_yaml(csv_path, yaml_path):
    """
    Transform combined_data.csv to testimonials.yml
    Converting binary category columns to explicit category arrays.
    """
    # Read CSV
    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Verify expected columns exist
    expected_cols = ["Name", "ReviewDate", "Review", "Question"] + CATEGORIES
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
    
    reviews = []
    
    # Process each row
    for idx, row in df.iterrows():
        if (idx + 1) % 5000 == 0:
            print(f"Processing row {idx + 1}/{len(df)}...")
        
        # Build categories array from binary columns
        categories_list = []
        for category in CATEGORIES:
            if row[category] == 1:
                categories_list.append(category)
        
        # Handle NaN values in Review text
        review_text = row["Review"]
        if pd.isna(review_text):
            review_text = ""
        else:
            review_text = str(review_text)
        
        # Handle NaN values in Question
        question = row["Question"]
        if pd.isna(question):
            question = ""
        else:
            question = str(question)
        
        # Create review object with all fields
        review = {
            "name": row["Name"],
            "date": row["ReviewDate"],
            "question": question,
            "text": review_text,
            "categories": categories_list
        }
        reviews.append(review)
    
    # Create root structure
    data = {"reviews": reviews}
    
    # Write to YAML
    print(f"Writing {yaml_path}...")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"✓ Transformation complete!")
    print(f"  Total reviews: {len(reviews)}")
    print(f"  Output file: {yaml_path}")

if __name__ == "__main__":
    csv_path = "combined_data.csv"
    yaml_path = "testimonials.yml"
    
    transform_csv_to_yaml(csv_path, yaml_path)
