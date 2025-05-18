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
        # ... (существующие запросы) ...
        "Есть ли в этом месяце тимбилдинг для отдела IT?",
        # Новые запросы для дней рождения
        "Найди дни рождения сегодня",
        "Покажи дни рождения этой недели",
        # ... (остальные запросы на ДР) ...
        "у кого из сотрудников отдела кадров день рождения в июне и они младше 30",
        # Новые запросы для задач
        "Найди мои задачи на сегодня",
        "Покажи задачи с дедлайном на этот месяц",
        "Какие у меня невыполненные задачи по проекту Alpha?",
        "Найди задачи с высоким приоритетом",
        "Покажи задачи, назначенные на Петрова Иванова",
        "Какие задачи просрочены?",
        "Найди задачи, в которых я участник", # "участник" - не сущность, но интент должен быть check_task
        "Покажи мои напоминания на завтра",
        "Какие задачи в статусе “в процессе”?",
        "Найди задачи с тегом “отчет” для проекта Гамма",
        "Покажи задачи на следующую неделю назначенные на Сидорова",
        "Найди задачи, созданные в прошлом месяце Ивановым",
        "Какие задачи без дедлайна у Петрова?",
        "Покажи все завершённые задачи за сегодня по проекту Омега",
        "Найди мои задачи, требующие согласования менеджера",
        "Мои открытые задачи с низким приоритетом и тегом документация"
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
                    confidence_val = entity.get('confidence_entity', entity.get('confidence'))
                    confidence_str = f", Confidence: {confidence_val:.4f}" if isinstance(confidence_val, float) else ""
                    role_str = f", Role: {entity.get('role')}" if entity.get('role') else ""
                    print(f"    - Тип: {entity.get('entity')}, Значение: '{entity.get('value')}'{confidence_str}{role_str}")
            else:
                print("  Сущности: не найдены")
            # print(json.dumps(nlu_result, indent=2, ensure_ascii=False))
        print("-" * 30)