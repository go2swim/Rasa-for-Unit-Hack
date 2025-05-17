from typing import Any, Text, Dict, List
import logging

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

# from rasa_sdk.events import SlotSet, UserUtteranceReverted # Не используются в текущей версии

logger = logging.getLogger(__name__)


class ActionProcessRequest(Action):
    def name(self) -> Text:
        return "action_process_request"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        intent_name = tracker.latest_message['intent'].get('name')
        entities = tracker.latest_message.get('entities', [])  # Убедимся, что entities всегда список

        # Формируем структурированные данные для возможной отправки вовне
        extracted_data = {
            "intent": intent_name,
            "entities": [],
            "text": tracker.latest_message.get('text')
        }

        # Сообщение для логирования и ответа пользователю (для демонстрации)
        log_message_parts = [f"Получен запрос с интентом: {intent_name}"]

        if not entities:
            log_message_parts.append("- Сущности не найдены.")
        else:
            log_message_parts.append("Извлеченные сущности:")
            for entity in entities:
                entity_info = {"entity": entity['entity'], "value": entity['value']}
                if 'group' in entity:  # для regex entities
                    entity_info['group'] = entity['group']
                if 'role' in entity:  # для roles
                    entity_info['role'] = entity['role']

                extracted_data["entities"].append(entity_info)
                log_message_parts.append(
                    f"- {entity['entity']}: {entity['value']} (confidence: {entity.get('confidence_entity', 'N/A'):.2f})")

        final_log_message = "\n".join(log_message_parts)
        logger.info(f"Processing request: {tracker.latest_message.get('text')}\n{final_log_message}")
        logger.info(f"Data to send to backend: {extracted_data}")

        # Ответ пользователю (для демонстрации)
        # dispatcher.utter_message(text=f"Обрабатываю ваш запрос: {tracker.latest_message.get('text')}")
        # dispatcher.utter_message(text=final_log_message) # Можно закомментировать, если не нужен такой подробный ответ в чате

        # Пример специфичной логики для search_person
        if intent_name == "search_person":
            # Собираем все значения для сущности 'name'
            names_found = [e['value'] for e in extracted_data["entities"] if e['entity'] == 'name']
            departments_found = [e['value'] for e in extracted_data["entities"] if e['entity'] == 'department']
            projects_found = [e['value'] for e in extracted_data["entities"] if e['entity'] == 'project']

            # Для простоты берем первое найденное имя, отдел, проект
            name_query = names_found[0] if names_found else "не указано"
            department_query = departments_found[0] if departments_found else "не указан"
            project_query = projects_found[0] if projects_found else "не указан"

            # Это сообщение можно использовать для отладки или как часть ответа
            # dispatcher.utter_message(
            #     text=f"Ищу сотрудника: Имя/Фамилия: '{name_query}', Отдел: '{department_query}', Проект: '{project_query}'."
            # )

            # Здесь ваша логика обращения к БД или API для поиска сотрудника
            # response_from_db = self.query_employee_db(name_query, department_query, project_query)
            # dispatcher.utter_message(text=response_from_db)
            # Для хакатона: просто подтверждаем получение данных
            dispatcher.utter_message(
                text=f"✅ Запрос на поиск сотрудника '{name_query}' (отдел: '{department_query}', проект: '{project_query}') принят.")


        elif intent_name == "search_event":
            event_names_found = [e['value'] for e in extracted_data["entities"] if e['entity'] == 'event_name']
            dates_found = [e['value'] for e in extracted_data["entities"] if e['entity'] == 'date']
            event_query = event_names_found[0] if event_names_found else "не указано"
            date_query = dates_found[0] if dates_found else "не указана"
            dispatcher.utter_message(
                text=f"✅ Запрос на поиск мероприятия '{event_query}' (дата: '{date_query}') принят.")

        # Добавьте обработку других интентов по аналогии
        else:
            # Общий ответ, если для интента нет специфичной логики выше
            dispatcher.utter_message(text=f"✅ Ваш запрос (интент: {intent_name}) принят к обработке.")

        # В реальном приложении здесь бы мог быть вызов вашего API:
        # requests.post("URL_ВАШЕГО_БЭКЕНДА", json=extracted_data)

        return []

    # def query_employee_db(self, name, department, project):
    #     # Заглушка для метода обращения к БД
    #     # В реальном приложении здесь будет код для запроса к вашей базе данных
    #     # Например, используя psycopg2, SQLAlchemy, requests к вашему API и т.д.
    #     logger.info(f"DB Query (simulated): Searching for Name='{name}', Department='{department}', Project='{project}'")
    #     # Пример ответа
    #     if name != "не указано":
    #         return f"Информация по сотруднику '{name}' найдена (симуляция)."
    #     return "Недостаточно данных для поиска сотрудника (симуляция)."