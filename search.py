import random
import pandas as pd
import numpy as np
import re


class Document:
    def __init__(self, title, text):
        # можете здесь какие-нибудь свои поля подобавлять
        self.title = title
        self.text = text
        self.words_found = []

    def format(self, query):
        # возвращает пару тайтл-текст, отформатированную под запрос
        return [self.title, self.text + ' ...', self.words_found]


index = []


def build_index():
    # данные взяты https://www.kaggle.com/neisse/scrapped-lyrics-from-6-genres
    # спасибо @atlant63 за препроцессинг

    artist_df = pd.read_csv('artists-data.csv')
    lyrics_df = pd.read_csv('lyrics-data.csv')

    # определяю список ненужных столбцов для удаления
    columns_to_delete = (set(lyrics_df.columns) | set(artist_df.columns)) - set(['Artist', 'SName', 'Lyric'])

    # датафрейм в котором хранятся название исполнителя, название песни и слова
    resulting_df = pd.merge(lyrics_df, artist_df, left_on='ALink', right_on='Link').drop(columns_to_delete, axis=1)

    # избавляюсь от слишком большого количества строк - для этого
    # создаю список случайных индексов для результирующего датафрейма
    np.random.seed(42)
    indexes = np.random.randint(low=0, high=len(resulting_df), size=100000)

    # произвожу сэмплирование, избавляюсь пустых строк, избавляюсь от дубликатов
    resulting_df = resulting_df.loc[indexes].dropna().drop_duplicates()

    for row in resulting_df.values:
        artist_song = row[2] + ' - ' + row[0]
        lyric = row[1][:300]
        index.append(Document(artist_song, lyric))


def score(query, doc):
    # возвращает какой-то скор для пары запрос-документ
    # больше -- релевантнее

    """Оценка 1

    # количество слов из запроса встретившихся в документе
    t = 0
    for i in query.lower().split(' '):
        # если встречается в title, даем больший скор
        if i in doc.title.lower().split(' '):
            t += 1
        elif i in doc.text.lower().split(' '):
            t += 0.5

    return t / len(query.split(' '))"""

    """Оценка 2
    t = 0

    # проверка вхождения запроса целиком - макс балл
    t += doc.title.lower().count(query.lower())
    t += doc.text.lower().count(query.lower()) * 0.9

    for i in query.lower().split(' '):
        t += doc.title.lower().count(i) * 0.5
        t += doc.text.lower().count(i) * 0.4

    return t / (len(doc.text.split(' ')) + len(doc.title.split(' ')))"""

    t = 0
    # веса для попадания
    # 1) всего запроса в тайтле
    # 2) всего запроса в тексте
    # 3) слова в тайтле
    # 4) слова в тексте
    # если брать коэффиценты больше 1, есть вероятность что функция может выдать значение больше 1,
    # но в реальности почти невозможно
    weights = [1.9, 0.9, 0.5, 0.4]

    # проверка вхождения запроса целиком - макс балл
    t += doc.title.lower().count(query.lower()) * weights[0]
    t += doc.text.lower().count(query.lower()) * weights[1]

    for i in query.lower().split(' '):
        # ограничиваем максимальное значимое количество вхождений пятью
        t += min(5, doc.title.lower().count(i)) * weights[2]
        t += min(5, doc.text.lower().count(i)) * weights[3]

    return t / (len(doc.text.split(' ')) + len(doc.title.split(' ')))


def retrieve(query):
    # возвращает начальный список релевантных документов
    # (желательно, не бесконечный)
    candidates = []

    """Иерархия"""
    """
    1) документы с полным вхождением запроса, например AC/DC - Back In Black
    2) документы содержащие все слова из запроса отдельно
    3) документы содержащие некоторые слова из запроса
    """

    # добавим первые элементы с вхождением полного текста
    # 1) документы с полным вхождением запроса, например AC/DC - Back In Black
    for doc in index:
        doc.words_found = []

        if query in doc.title.lower() or query in doc.text.lower():
            # для отображения слов в html
            doc.words_found.append(query)
            #

            candidates.append(doc)

    # если количество слов больше 1, важнее если они будут встречаться подряд, учитываем в метрике
    # если количество слов = 1 берем всё что содержит это слово и добавляем в candidates
    # 2) документы содержащие все слова из запроса
    N = 10

    if len(query.split(' ')) != 1:
        for doc in index:
            t = 0

            """if query in doc.title.lower() or query in doc.text.lower():
                t += doc.title.lower().count(i)

                candidates.append(doc)

                # для отображения слов в html
                doc.words_found.append(query)
                #

            else:"""
            stop = False
            k = 0
            for i in query.lower().split(' '):


                # не берем запросы в которых нет хотя бы n слов
                if doc.title.lower().count(i) > 0 or doc.text.lower().count(i) > 0:
                    t += doc.title.lower().count(i)
                    t += doc.text.lower().count(i)
                else:
                    k += 1
                    stop = True
                    break

                # для отображения слов в html
                doc.words_found.append((i, t))
                #

            # !!!! кол-во нужных слов / кол-во слов
            if t > 0 and not stop:
                candidates.append(doc)

            else:
                pass
                # 3) документы содержащие нектороые слова из запроса
                """for i in query.lower().split(' '):

                    # берем запросы в которых есть хотя бы одно слово запроса
                    if doc.title.lower().count(i) >= 0 or doc.text.lower().count(i) >= 0:
                        t += doc.title.lower().count(i)
                        t += doc.text.lower().count(i)

                    # для отображения слов в html
                    doc.words_found.append((i, t))"""

    return candidates[:100]
