# Модель для AI-ассистента Интересыч (https://github.com/ArtemToporkov/very-interesting-case)

python 3.9
````
pip install 'rasa[spacy]'
pip install rasa-sdk
pip install spacy
python -m spacy download ru_core_news_sm
pip install 'rasa[transformers]'
````

Запуск api (для бека):
````
rasa run --enable-api --cors "*" -p 5005
````

Запуск диалога в консоли:
````
rasa run actions
rasa shell
````

Обучение модели (после изменений):
````
rasa train
````