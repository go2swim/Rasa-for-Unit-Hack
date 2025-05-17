import requests
import json

rasa_url = "http://localhost:5005/model/parse"


def get_nlu_data(text_query):
    payload = {"text": text_query}
    try:
        response = requests.post(rasa_url, json=payload)
        response.raise_for_status()  # Проверка на HTTP ошибки
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при обращении к Rasa NLU API: {e}")
        return None


if __name__ == "__main__":
    queries = [
        "Найди Анну Смирнову из IT",
        "Какие мероприятия завтра?",
        "У кого день рождения в июне?",
        "Привет",
        "Покажи мне Волкова Михаила",
        "телефон Кузнецова",
        "Сотрудник Лебедева Наталья из бухгалтерии в проекте Гамма"
    ]

    for query in queries:
        print(f"\nЗапрос: {query}")
        nlu_result = get_nlu_data(query)
        if nlu_result:
            print("Результат NLU:")
            print(f"  Текст: {nlu_result.get('text')}")
            intent = nlu_result.get('intent', {})
            print(f"  Интент: {intent.get('name')} (Confidence: {intent.get('confidence'):.4f})")

            entities = nlu_result.get('entities', [])
            if entities:
                print("  Сущности:")
                for entity in entities:
                    print(f"    - Тип: {entity.get('entity')}, Значение: '{entity.get('value')}', "
                          f"Confidence: {entity.get('confidence_entity', 'N/A'):.4f}")
            else:
                print("  Сущности: не найдены")
            # print(json.dumps(nlu_result, indent=2, ensure_ascii=False)) # Раскомментируйте для полного вывода JSON
        print("-" * 30)