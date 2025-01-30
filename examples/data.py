import pandas as pd

nea_data = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/Figure-Friday/refs/heads/main/2025/week-4/Post45_NEAData_Final.csv"
)
nea_data["Age"] = nea_data["nea_grant_year"] - nea_data["birth_year"]
