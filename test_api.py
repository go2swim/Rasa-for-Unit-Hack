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
        # ... (существующие запросы для других интентов) ...
        "Найди мои задачи, требующие согласования менеджера",
        "Мои открытые задачи с низким приоритетом и тегом документация",
        # Новые запросы для календаря
        "Покажи мой календарь на сегодня",
        "Какие у меня встречи завтра?",
        "Найди свободные слоты в моём календаре на этой неделе",
        "Покажи расписание Петрова Ивана на 20 мая",
        "Какие у меня занятые часы сегодня?",
        "Найди временные окна без встреч в моем календаре в следующем месяце",
        "Покажи все совещания с участием Петрова в моём календаре на эту неделю",
        "Какие у меня встречи на следующую неделю?",
        "Найди конфликты в моём расписании на завтра",
        "Покажи, во сколько у меня обеденный перерыв",
        "Какие задачи и встречи у меня запланированы на пятницу?",
        "Найди свободное время для двухчасовой встречи завтра",
        "Покажи календарь Ольги на завтра с выделением загруженных дней",  # "загруженных дней" - не сущность
        "Какие у меня зарезервированы конференц-залы на сегодня?",
        "Найди утренние встречи до 12:00 в моём календаре на понедельник",
        "Свободен ли я завтра в 3 часа дня?",
        "Занят ли Сидоров для часовой встречи после обеда в среду?"
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
                    confidence_val_raw = entity.get('confidence_entity', entity.get('confidence'))
                    confidence_str = ""
                    if confidence_val_raw is not None:
                        try:
                            confidence_str = f", Confidence: {float(confidence_val_raw):.4f}"
                        except ValueError:
                            confidence_str = f", Confidence: N/A (raw: {confidence_val_raw})"

                    role_str = f", Role: {entity.get('role')}" if entity.get('role') else ""
                    print(
                        f"    - Тип: {entity.get('entity')}, Значение: '{entity.get('value')}'{confidence_str}{role_str}")
            else:
                print("  Сущности: не найдены")
            # print(json.dumps(nlu_result, indent=2, ensure_ascii=False))
        print("-" * 30)