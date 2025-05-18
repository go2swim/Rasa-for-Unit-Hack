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
        "Сотрудник Лебедева Наталья из бухгалтерии в проекте Гамма",
        "Какие корпоративные тренинги для отдела IT будут на следующей неделе в Москве?",
        "Создай внутренний ивент Урок йоги на 10 июня в 18:00 в спортзале",
        "Добавь меня в список участников встречи Общая планёрка 25 мая",
        "Когда будет следующий хакатон и кто его организует?",
        "Покажи все онлайн‑эвенты на следующей неделе",
        "Найди внутрикорпоративное мероприятие, связанное с благотворительностью",
        "Напомни всем участникам о встрече SprintReview за час до начала",
        "Есть ли в этом месяце тимбилдинг для отдела IT?"
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
                    confidence_val = entity.get('confidence_entity', entity.get('confidence')) # DIET sometimes uses 'confidence'
                    confidence_str = f", Confidence: {confidence_val:.4f}" if isinstance(confidence_val, float) else ""
                    role_str = f", Role: {entity.get('role')}" if entity.get('role') else ""
                    print(f"    - Тип: {entity.get('entity')}, Значение: '{entity.get('value')}'{confidence_str}{role_str}")
            else:
                print("  Сущности: не найдены")
            # Для полного вывода можно раскомментировать следующую строку:
            # print(json.dumps(nlu_result, indent=2, ensure_ascii=False))
        print("-" * 30)