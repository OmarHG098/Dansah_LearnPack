import pandas as pd
from functions import pull_reviews, concat_dataframes

# -------------------
# 1. Load data
# -------------------
df_careerkarma = pd.read_csv("/workspaces/Dansah_LearnPack/careerkarma_reviews.csv")
df_careerkarma = pull_reviews(df_careerkarma)

df_bootcampranking = pd.read_csv("/workspaces/Dansah_LearnPack/bootcamprankings_reviews.csv")
df_bootcampranking = pull_reviews(df_bootcampranking)

df_coursereport = pd.read_csv("/workspaces/Dansah_LearnPack/course_report_reviews.csv")
df_coursereport = pull_reviews(df_coursereport)

df_switchup = pd.read_csv("/workspaces/Dansah_LearnPack/switchup_reviews.csv")
df_switchup = pull_reviews(df_switchup)

df_nps = pd.read_csv("/workspaces/Dansah_LearnPack/nps_reviews.csv")
df_nps = pull_reviews(df_nps)

# -------------------
# 2. Concatenate the Data
# -------------------

df = concat_dataframes([df_nps, df_switchup, df_coursereport, df_bootcampranking, df_careerkarma])

# -------------------
# 3. Save the Data
# -------------------

df.to_csv("combined_data.csv", index=False, encoding="utf-8")