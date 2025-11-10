# %% [markdown]
# # Практическое задание № 2. Нейронные сети
# 



# %% [markdown]
# ## Прогнозирование цены на жилье с помощью нейросетевой регрессионной модели
# 
# Необходимо по имеющимся данным о ценах на жильё предсказать окончательную цену каждого дома с учетом характеристик домов с использованием нейронной сети. Описание набора данных  содержит 80 классов (набор переменых) классификации оценки типа жилья, и находится в файле `data_description.txt`.
# 
# В работе требуется дополнить раздел «Моделирование» в подразделе «Построение и обучение модели» создать и инициализировать последовательную модель нейронной сети с помощью фрэймворков тренировки нейронных сетей как: Torch или Tensorflow. Скомпилировать нейронную сеть выбрав функцию потерь и оптимизатор соответственно. Оценить точность полученных результатов. Вывести предсказанные данные о продаже. 
# 
# 
# ### Импорт библиотек
# Импортируем необходимые библиотеки:

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# %% [markdown]
# ### Считываем набор данных
# 
# 
# Загрузим набор данных и присвоим следующими переменные:
# 
# * `train_data`: данные, используемые для обучения модели
# * `test_data`: данные, используемые для проверки модели

# %%
train_data = pd.read_csv('/data/notebook_files/train.csv')
test_data = pd.read_csv('/data/notebook_files/test.csv')

# %% [markdown]
# ## Подготовка данных
# ### Отобразим обучающие и проверочные данные:

# %%
train_data.head()

# %%
test_data.head()

# %% [markdown]
# Как можно видеть, `train_data` имеет на один столбец больше, чем `test_data`, это столбец `SalePrice`, для обучения модели перед применением ее для предсказания меток в test_data.

# %% [markdown]
# ### Проверяем нет ли тестовые данные пустых значений значений (Nan)
# 
# Построим функцию `def missing_value_checker` для проверки и подсчёта пропущеных значений в test_data. А также выведем тип данных этих значений.
# 

# %%
def missing_value_checker(data):
    list = []
    for feature, content in data.items():
        if data[feature].isnull().values.any():
            
            sum = data[feature].isna().sum()

            type = data[feature].dtype

            print (f'{feature}: {sum}, type: {type}')
            
            list.append(feature)
    print(list)

    print(len(list))

missing_value_checker(test_data)

# %% [markdown]
# Проверяем какие признаки в таблице можно оставить, а какие удалить. Если пропущенных значений слишком много, то удалим признак. Если их небольшое количество, то заполним `mean` или `median` для чисел, новая категория `missing` для строковых объектов.
# 
# В соответствии с этим:
# 
# – удалим ['Alley', 'FireplaceQu', 'PoolQC', 'Fence', 'MiscFeature'];
# 
# – заполним числовое отсутствующее значение значением `mean`;
# 
# – заполним строковое отсутствующее значение значением `missing`.

# %%
test_edited = test_data.drop(['Alley','FireplaceQu','PoolQC', 'Fence', 'MiscFeature'], axis=1)
train_edited = train_data.drop(['Alley','FireplaceQu','PoolQC', 'Fence', 'MiscFeature'], axis=1)

def nan_filler(data):
    for label, content in data.items():
        if pd.api.types.is_numeric_dtype(content):
            data[label] = content.fillna(content.median())
        else:
            data[label] = content.astype("category").cat.as_ordered()
            data[label] = pd.Categorical(content).codes+1

nan_filler(test_edited)
nan_filler(train_edited)

# %% [markdown]
# ### Перепроверим наши данные:

# %%
missing_value_checker(test_edited)

# %%
missing_value_checker(train_edited)

# %%
train_edited.shape, test_edited.shape

# %%
test_edited.info()

# %%
train_edited.info()

# %% [markdown]
# ### Разделим данные
# 
# Поскольку мы не знаем метку (Цена) тестовых данных, для оценки модели, чтобы получить лучшую модель перед прогнозированием тестовых данных, разделим данные в файле train.scv на обучающие и проверочные данные, соотношение составляет 20%.

# %%
X = train_edited.drop('SalePrice', axis=1)
y = train_edited['SalePrice']

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size = 0.2)

# %%
X_train.shape, test_edited.shape

# %% [markdown]
# ## Моделирование

# %% [markdown]
# ### Построение и обучение модели

# %% [markdown]
# 
# Создайте последовательную модель нейронной сети с помощью фрэймворков тренировки нейронных сетей как: Torch или Tensorflow. 

# %%
# from tensorflow import keras или import torch
model = Sequential(None)
# замените None на колличество входных полносвязных слоёв, колличество нейронов, колличество выходов
tf.random.set_seed(40) / torch.manual_seed(40) #Для обеспечения воспроизводимости результатов устанавливается функция seed

# %% [markdown]
# Скомпилируйте нейронную сеть, выбрав функцию потерь и оптимизатор соответственно.

# %%

model.compile() #Для оценки потерь и метрики рекомендую использовать метрики и функции потерь для регрессии.

# %% [markdown]
# Обучите модель на обучающих данных `X_train` и `y_train` задав гиперпараметры вашей модели нейронной сети, например количество эпох (epochs), размер мини-выборки (batch_size) и другие.

# %%
history = model.fit(X_train, y_train, None) #замените None на гиперпараметры вашей модели нейронной сети

# %% [markdown]
# **Оцените полученные результаты**

# %%
pd.DataFrame(history.history).plot()
plt.ylabel('xxxx')
plt.xlabel('yyyy')
print(history.history)

# %%
scores = None

# %% [markdown]
# ### Прогнозирование

# %%
preds = None
preds

# %%
#пример 
output = pd.DataFrame(
{
    'Id':test_data['Id'],
    'SalePrice': np.squeeze(preds)
})
output


# %% [markdown]
# ## Задание
# 
# 
# В задние представлено логика выполнения с использование tensorflow/keras. Выполнять можно как с использованием tensorflow/keras, так и pytorch.
# 
# 
# **При выполнении:**
# 
# Выведите отчет нейросетевой регрессионной модели, для  прогнозирование цены на жилье. 
# 
# 
# Подберите  разные комбинации гиперпараметров таким образом, чтобы получить лучший результат на тестовом наборе данных.
# 
# Попробуйте использовать разное количество нейронов на входном слое. Опишите достигнутый результат.
# 
# Добавьте в нейронную сеть скрытый слой с разным количеством нейронов.
# 
# Используйте разное количество эпох. Опишите достигнутый результат.
# 
# Используйте разные размеры мини-выборки (batch_size). Опишите достигнутый результат.
# 
# Попробуйте использовать разные значения оптимизатора `optimizers` и функции потерь `loss`. Сравните полученные результаты.
# 
# **Вопросы:**
# 
# Как выше перечисленные параметры влияют на полученный вами результат? 
# 
# Что такое эпоха (Epoch)? В чем отличие от итерации (Iteration)?
# 
# Что такое функция активации? Какие вам известны? Как и зачем используются в нейронной сети?
# 
# Что такое MSE(Mean Squared Error) - Средняя квадратичная ошибка? Что такое MAE(Mean Absolute Error)? Для чего используются.


