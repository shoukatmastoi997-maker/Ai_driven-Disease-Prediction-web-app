import pandas as pd
df = pd.read_csv('Disease/DiseaseandSymptoms.csv')
df.columns = df.columns.str.strip()
for col in df.columns:
    df[col] = df[col].astype(str).str.strip().str.lower()
df.replace('nan', pd.NA, inplace=True)
df.drop_duplicates(inplace=True)
print("Cleaned Data shape:", df.shape)
symptom_columns = [col for col in df.columns if col.startswith('Symptom')]
df['combined_symptoms'] = df[symptom_columns].values.tolist()
df_exploded = df.explode('combined_symptoms')
df_exploded = df_exploded.dropna(subset=['combined_symptoms'])
dummies = pd.get_dummies(df_exploded['combined_symptoms'])
binary_matrix = dummies.groupby(df_exploded.index).max()
df_final = pd.concat([df['Disease'], binary_matrix], axis=1)
print("Final Data Shape:", df_final.shape)
print(df_final.head())
df_final.to_csv("processed_disease_dataset.csv", index=False)
