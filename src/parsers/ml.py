from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from processing_description import processing_description
from preparation_data import df
import pickle

counter = 0
array_with_del = []
for i in range(df.shape[0]):
    if df.iloc[i]['specialization'] == 'Системный аналитик':
        if counter > 100:
            break
        counter += 1
        array_with_del.append(i)
df.drop(labels=array_with_del, axis=0, inplace=True)

new_descriptions = []
for description in df['vacancy_description']:
    new_descriptions.append(processing_description(description))
df['vacancy_description'] = new_descriptions

vect = TfidfVectorizer(sublinear_tf=True, norm='l2', ngram_range=(1, 2))
tmp_features = vect.fit(df['vacancy_description'])
file_tfidf = '../saved_tfidf.pkl'
pickle.dump(tmp_features, open(file_tfidf, 'wb'))
features = vect.transform(df['vacancy_description']).toarray()
model = LinearSVC(class_weight='balanced')
labels = df['category_id']
model.fit(features, labels)
file_model = '../saved_model.sav'
pickle.dump(model, open(file_model, 'wb'))
