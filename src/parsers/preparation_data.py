import pandas as pd

df = pd.read_csv('data.csv')
df = df.drop(columns=['vacancy_name', 'skills', 'company_name', 'grade', 'salary', 'is_online', 'vacancy_url',
                      'publication_date', 'city'])
df['category_id'] = df['specialization'].factorize()[0]
category_id_df = df[['specialization', 'category_id']].drop_duplicates().sort_values('category_id')
id_to_category = dict(category_id_df[['category_id', 'specialization']].values)

