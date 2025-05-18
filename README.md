# Rasa-for-Unit-Hack

python 3.9

````
pip install 'rasa[spacy]'
pip install rasa-sdk
pip install spacy
python -m spacy download ru_core_news_sm
pip install 'rasa[transformers] transformers'
````

Запуск api (для бека):
````
rasa run --enable-api --cors "*" -p 5005
````

Запуск:
````
rasa run actions
rasa shell
````

Перед тем как закоммитить:
````
rasa train
````