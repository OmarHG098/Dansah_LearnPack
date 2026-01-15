import pandas as pd
import re
import unicodedata
from datetime import datetime

categories = {
    "OnlinePlatform": ["online platform", "plataforma en línea", "virtual campus", "streaming", "plataforma online", "cloud", "plataforma"],
    "MentorsTeachers": ["mentor", "profesor", "teacher", "instructor", "docente", "mentors", "tutors", "teachers", "instructors", "profes", "mentores", "tutores", "profesores"],
    "Price": ["price", "cost", "affordable", "precio", "costo", "tuition", "cheap", "investment", "worth", "matrícula", "barato", "inversión", "vale la pena"],
    "CareerSupport": ["career", "job", "empleo", "bolsa de trabajo", "career support", "job search", "interview", "resume", "LinkedIn", "networking", "búsqueda de empleo", "entrevistas", "currículum", "apoyo laboral", "asesoría"],
    "ContentSyllabus": ["course", "syllabus", "curriculum", "temario", "contenido", "bootcamp", "program", "projects", "exercises", "learning", "knowledge", "classes", "clases", "proyectos", "ejercicios", "aprendizaje", "conocimientos"],
    "Job Guarantee": ["job guarantee", "garantía de empleo", "job placement", "empleo garantizado", "colocación laboral"],
    "FullStack": ["full stack", "frontend", "backend", "fullstack", "desarrollo full stack", "web development", "desarrollo web"],
    "Cybersecurity": ["cybersecurity", "ciberseguridad"],
    "DataScience": ["data science", "ciencia de datos", "machine learning", "ai", "inteligencia artificial"],
    "AppliedAI": ["applied ai", "inteligencia artificial aplicada", "ai program", "machine learning"],
    "Outcomes": ["outcome", "resultados", "empleo obtenido", "results", "success", "achieve", "goals", "exitos", "logros", "metas"],
    "Scholarships": ["scholarship", "beca", "financial aid", "ayuda financiera"],
    "Rigobot": ["rigobot"],
    "LearnPack": ["learnpack"]
}

def normalize_text(text):
    """Lowercase, remove accents, and strip extra spaces."""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text.strip()

def categorize_review(headline=None, body=None):
    """Return 1/0 per category for a review."""
    combined_text = f"{normalize_text(headline)} {normalize_text(body)}"
    result = {}
    for category, keywords in categories.items():
        result[category] = int(any(re.search(r"\b" + re.escape(normalize_text(k)) + r"\b", combined_text) for k in keywords))
    return result

def standardize_date(date_string):
    """
    Standardize various date formats to ISO format (YYYY-MM-DD).
    Handles: 'November 2, 2020', 'Nov 18, 2024', '3/18/2025', ISO 8601 timestamps.
    For timestamps, extracts just the date portion (e.g., '2024-10-07' from '2024-10-07T10:23:45Z' or '2024-10-07 10:23:45').
    Returns original string if unparseable (e.g., relative dates like '5 months ago').
    """
    if not date_string or str(date_string).lower() in ['unknown', 'nan', '', 'none']:
        return 'Unknown'
    
    date_string = str(date_string).strip()
    
    # Handle ISO 8601 timestamps - extract date portion only (handles both T and space separators)
    if 'T' in date_string or ' ' in date_string:
        try:
            # Split on 'T' or space and take first part
            iso_date = date_string.split('T')[0] if 'T' in date_string else date_string.split(' ')[0]
            return iso_date
        except:
            pass
    
    # Try platform-specific date formats
    formats = [
        '%B %d, %Y',      # November 2, 2020 (BootcampRankings)
        '%b %d, %Y',      # Nov 18, 2024 (CourseReport)
        '%m/%d/%Y',       # 3/18/2025 (SwitchUp)
        '%Y-%m-%d',       # ISO format (NPS)
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_string, fmt)
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # If no format matches, return original (e.g., '5 months ago' from CareerKarma)
    return date_string

def pull_reviews(df):
    """
    Extract Name + ReviewDate + Review + 16 category columns from platform CSV.
    Handles different column naming across platforms and standardizes dates.
    NPS reviews without names default to 'Anonymous'.
    """
    # Handle Name column (all platforms have it except NPS)
    if 'Name' not in df.columns:
        df['Name'] = 'Anonymous'
    
    # Find and standardize date column
    date_col = None
    for col in ['Date', 'Review_Date', 'updated_at']:
        if col in df.columns:
            date_col = col
            break
    
    if date_col:
        df['ReviewDate'] = df[date_col].apply(standardize_date)
    else:
        df['ReviewDate'] = 'Unknown'
    
    # Select columns in correct order: Name, ReviewDate, Review, then 16 categories (no duplicates)
    review_df = df[[
        'Name', 'ReviewDate', 'Review',
        'OnlinePlatform', 'MentorsTeachers', 'Price', 'CareerSupport', 'ContentSyllabus',
        'Job Guarantee', 'FullStack', 'Cybersecurity', 'DataScience', 'AppliedAI',
        'Outcomes', 'Scholarships', 'Rigobot', 'LearnPack'
    ]]
    
    return review_df

def concat_dataframes(df_list:list):
    full_data = pd.concat(df_list, axis=0)

    return full_data
