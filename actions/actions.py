from typing import Any, Text, Dict, List
import logging
import json

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet  # Можем использовать для установки слотов, если понадобится

logger = logging.getLogger(__name__)


class ActionProcessRequest(Action):
    def name(self) -> Text:
        return "action_process_request"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        intent_name = tracker.latest_message['intent'].get('name')
        entities_from_tracker = tracker.latest_message.get('entities', [])

        # Формируем структурированные данные для отправки на бэкенд
        # Этот JSON будет содержать все детали для вашего бэкенда
        extracted_data_for_backend = {
            "intent": intent_name,
            "entities": [],  # Будет заполнен сущностями с их ролями
            "text": tracker.latest_message.get('text')
        }

        # Логирование и подготовка информации для ответа (если он нужен от action)
        log_message_parts = [f"Получен запрос с интентом: {intent_name}"]

        if not entities_from_tracker:
            log_message_parts.append("- Сущности не найдены.")
        else:
            log_message_parts.append("Извлеченные сущности:")
            for entity in entities_from_tracker:
                entity_info_for_backend = {
                    "entity": entity['entity'],
                    "value": entity['value'],
                    "start": entity.get('start'),
                    "end": entity.get('end')
                }
                if 'confidence_entity' in entity:
                    entity_info_for_backend['confidence'] = round(entity['confidence_entity'], 4)
                if 'role' in entity:
                    entity_info_for_backend['role'] = entity['role']
                if 'group' in entity:
                    entity_info_for_backend['group'] = entity['group']

                extracted_data_for_backend["entities"].append(entity_info_for_backend)

                # Формируем строку для лога
                role_str = f" (Роль: {entity['role']})" if 'role' in entity else ""
                log_message_parts.append(
                    f"- Тип: {entity['entity']}{role_str}, Значение: '{entity['value']}'"
                    f" (Confidence: {entity.get('confidence_entity', 'N/A'):.2f})"
                )

        final_log_message = "\n".join(log_message_parts)
        logger.info(f"Processing request: {tracker.latest_message.get('text')}\n{final_log_message}")
        # Логируем JSON, который будет отправлен на бэкенд (или который бэкенд получит от /model/parse)
        logger.info(
            f"Data structure for backend (from /model/parse or similar action output):\n{json.dumps(extracted_data_for_backend, ensure_ascii=False, indent=2)}")

        # --- Формирование ответа пользователю (для демонстрации в чате) ---
        # Этот блок нужен, если вы хотите, чтобы Rasa action отвечал в чат.
        # Если вы используете только /model/parse, этот блок не будет выполняться для внешних API запросов.

        response_message = f"✅ Ваш запрос (интент: {intent_name}) принят. "
        details_parts = []

        if intent_name == "search_person":
            # Собираем параметры из extracted_data_for_backend для формирования красивого ответа
            # Бэкенд будет использовать сам extracted_data_for_backend
            temp_search_params = {}
            projects_lead = []
            projects_participant = []
            skills = []

            for ent in extracted_data_for_backend["entities"]:
                entity_type = ent["entity"]
                entity_value = ent["value"]
                entity_role = ent.get("role")

                if entity_type == "project":
                    if entity_role == "lead":
                        projects_lead.append(entity_value)
                    else:  # Если роли нет или она другая, считаем участником
                        projects_participant.append(entity_value)
                elif entity_type == "skill":
                    skills.append(entity_value)
                elif entity_type not in temp_search_params:
                    temp_search_params[entity_type] = entity_value
                elif isinstance(temp_search_params[entity_type], list):
                    temp_search_params[entity_type].append(entity_value)
                else:
                    temp_search_params[entity_type] = [temp_search_params[entity_type], entity_value]

            if temp_search_params.get("name"): details_parts.append(f"Имя/ФИО: '{temp_search_params.get('name')}'")
            if temp_search_params.get("department"): details_parts.append(
                f"Отдел: '{temp_search_params.get('department')}'")
            if projects_participant: details_parts.append(f"Участие в проекте(ах): '{', '.join(projects_participant)}'")
            if projects_lead: details_parts.append(f"Руководство проектом(ами): '{', '.join(projects_lead)}'")
            if skills: details_parts.append(f"Навыки: '{', '.join(skills)}'")
            if temp_search_params.get("age_exact"): details_parts.append(
                f"Возраст: '{temp_search_params.get('age_exact')}'")
            if temp_search_params.get("age_older_than"): details_parts.append(
                f"Старше: '{temp_search_params.get('age_older_than')}' лет")
            if temp_search_params.get("age_younger_than"): details_parts.append(
                f"Младше: '{temp_search_params.get('age_younger_than')}' лет")
            if temp_search_params.get("birthday_specifier"): details_parts.append(
                f"День рождения: '{temp_search_params.get('birthday_specifier')}'")

            if details_parts:
                response_message = f"✅ Запрос на поиск сотрудника принят. Критерии: {'; '.join(details_parts)}."
            else:
                response_message = "✅ Запрос на поиск сотрудника принят (без уточняющих критериев)."

        elif intent_name == "search_event":
            event_name = next(
                (e['value'] for e in extracted_data_for_backend["entities"] if e['entity'] == 'event_name'),
                "не указано")
            event_date = next((e['value'] for e in extracted_data_for_backend["entities"] if e['entity'] == 'date'),
                              "не указана")
            response_message = f"✅ Запрос на поиск мероприятия '{event_name}' (дата: '{event_date}') принят."

        elif intent_name == "find_birthday":
            person_name = next((e['value'] for e in extracted_data_for_backend["entities"] if e['entity'] == 'name'),
                               "всех сотрудников")
            birthday_date = next((e['value'] for e in extracted_data_for_backend["entities"] if e['entity'] == 'date'),
                                 "не указана")
            response_message = f"✅ Запрос на поиск дней рождения для '{person_name}' (дата/период: '{birthday_date}') принят."

        elif intent_name == "check_task":
            task_name = next((e['value'] for e in extracted_data_for_backend["entities"] if e['entity'] == 'task_name'),
                             "не указана")
            project_name = next(
                (e['value'] for e in extracted_data_for_backend["entities"] if e['entity'] == 'project'), "не указан")
            task_date = next((e['value'] for e in extracted_data_for_backend["entities"] if e['entity'] == 'date'),
                             "не указана")
            response_message = f"✅ Запрос на проверку задачи '{task_name}' (проект: '{project_name}', дата: '{task_date}') принят."

        elif intent_name == "check_employment_calendar":
            person_name = next((e['value'] for e in extracted_data_for_backend["entities"] if e['entity'] == 'name'),
                               "не указан")
            calendar_date = next((e['value'] for e in extracted_data_for_backend["entities"] if e['entity'] == 'date'),
                                 "не указана")
            response_message = f"✅ Запрос на проверку календаря занятости для '{person_name}' (дата: '{calendar_date}') принят."

        elif intent_name == "greet":
            response_message = "Привет! Чем могу помочь?"
        elif intent_name == "goodbye":
            response_message = "До свидания!"
        elif intent_name == "affirm":
            response_message = "Понял."
        elif intent_name == "deny":
            response_message = "Хорошо."
        elif intent_name == "bot_challenge":
            response_message = "Я AI-ассистент, созданный для помощи в корпоративных задачах."
        # Добавьте другие специфичные ответы, если необходимо

        dispatcher.utter_message(text=response_message)

        # Если вы хотите, чтобы это действие возвращало структурированные данные через API Rasa (а не только через /model/parse),
        # то можно использовать dispatcher.utter_custom_json(extracted_data_for_backend)
        # Но для вашего случая (использование /model/parse) это не требуется.

        return []  # Никаких событий для изменения диалога не возвращаем, если это чисто NLU + Rules