from typing import Any, Text, Dict, List
import logging
import json

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

logger = logging.getLogger(__name__)


class ActionProcessRequest(Action):
    def name(self) -> Text:
        return "action_process_request"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        intent_name = tracker.latest_message['intent'].get('name')
        entities_from_tracker = tracker.latest_message.get('entities', [])
        latest_message_text = tracker.latest_message.get('text')

        extracted_data_for_backend = {
            "intent": intent_name,
            "entities": [],
            "text": latest_message_text
        }

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
                confidence_val_raw = entity.get('confidence_entity', entity.get('confidence'))
                if confidence_val_raw is not None:
                    try:
                        entity_info_for_backend['confidence'] = round(float(confidence_val_raw), 4)
                    except ValueError:
                        logger.warning(f"Could not convert confidence to float for entity: {entity}")

                if 'role' in entity:
                    entity_info_for_backend['role'] = entity['role']
                if 'group' in entity:
                    entity_info_for_backend['group'] = entity['group']

                extracted_data_for_backend["entities"].append(entity_info_for_backend)

                role_str = f" (Роль: {entity['role']})" if 'role' in entity else ""
                group_str = f" (Группа: {entity['group']})" if 'group' in entity else ""

                confidence_log_str = ""
                if 'confidence' in entity_info_for_backend:
                    confidence_log_str = f" (Confidence: {entity_info_for_backend['confidence']:.2f})"

                log_message_parts.append(
                    f"- Тип: {entity['entity']}{role_str}{group_str}, Значение: '{entity['value']}'{confidence_log_str}"
                )

        final_log_message = "\n".join(log_message_parts)
        logger.info(f"Processing request: {latest_message_text}\n{final_log_message}")
        logger.info(
            f"Data structure for backend (from /model/parse or similar action output):\n{json.dumps(extracted_data_for_backend, ensure_ascii=False, indent=2)}")

        response_message = f"✅ Ваш запрос (интент: {intent_name}) принят. "
        details_parts = []

        if intent_name == "search_person":
            temp_search_params = {}
            projects_lead = []
            projects_participant = []
            skills = []
            birthday_specifiers = []  # Can be multiple

            for ent in extracted_data_for_backend["entities"]:
                entity_type = ent["entity"]
                entity_value = ent["value"]
                entity_role = ent.get("role")

                if entity_type == "project":
                    if entity_role == "lead":
                        projects_lead.append(entity_value)
                    else:
                        projects_participant.append(entity_value)
                elif entity_type == "skill":
                    skills.append(entity_value)
                elif entity_type == "birthday_specifier":
                    birthday_specifiers.append(entity_value)
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
            if birthday_specifiers: details_parts.append(f"День рождения: '{', '.join(birthday_specifiers)}'")

            if details_parts:
                response_message = f"✅ Запрос на поиск сотрудника принят. Критерии: {'; '.join(details_parts)}."
            else:
                response_message = "✅ Запрос на поиск сотрудника принят (без уточняющих критериев)."

        elif intent_name == "search_event":
            event_params = {}
            dates = []
            for ent in extracted_data_for_backend["entities"]:
                if ent["entity"] == "date":
                    dates.append(ent["value"])
                elif ent["entity"] not in event_params:
                    event_params[ent["entity"]] = ent["value"]
                elif isinstance(event_params[ent["entity"]], list):
                    event_params[ent["entity"]].append(ent["value"])
                else:
                    event_params[ent["entity"]] = [event_params[ent["entity"]], ent["value"]]

            if event_params.get("event_name"): details_parts.append(f"Название: '{event_params.get('event_name')}'")
            if event_params.get("event_category"): details_parts.append(
                f"Категория: '{event_params.get('event_category')}'")
            if dates: details_parts.append(f"Дата/период: '{', '.join(dates)}'")
            if event_params.get("location"): details_parts.append(f"Место: '{event_params.get('location')}'")
            if event_params.get("department"): details_parts.append(f"Для отдела: '{event_params.get('department')}'")
            if event_params.get("organizer"): details_parts.append(f"Организатор: '{event_params.get('organizer')}'")

            action_taken_msg = "Запрос по мероприятию принят. "
            # ... (action keyword checks remain the same)
            if "создай" in latest_message_text.lower() or "запланируй" in latest_message_text.lower() or "организуй" in latest_message_text.lower():
                action_taken_msg = "Запрос на создание/планирование мероприятия принят. "
            elif "добавь" in latest_message_text.lower() or "запиши меня" in latest_message_text.lower():
                action_taken_msg = "Запрос на добавление участника принят. "
            elif "напомни" in latest_message_text.lower():
                action_taken_msg = "Запрос на напоминание о мероприятии принят. "
            elif "удали" in latest_message_text.lower():
                action_taken_msg = "Запрос на удаление мероприятия принят. "
            elif "перенеси" in latest_message_text.lower():
                action_taken_msg = "Запрос на перенос мероприятия принят. "

            if details_parts:
                response_message = f"✅ {action_taken_msg}Критерии: {'; '.join(details_parts)}."
            else:
                response_message = f"✅ {action_taken_msg}Уточните детали мероприятия."

        elif intent_name == "find_birthday":
            birthday_params = {}
            birthday_specifiers = []
            dates = []
            for ent in extracted_data_for_backend["entities"]:
                if ent["entity"] == "birthday_specifier":
                    birthday_specifiers.append(ent["value"])
                elif ent["entity"] == "date":
                    dates.append(ent["value"])
                elif ent["entity"] not in birthday_params:
                    birthday_params[ent["entity"]] = ent["value"]
                elif isinstance(birthday_params[ent["entity"]], list):
                    birthday_params[ent["entity"]].append(ent["value"])
                else:
                    birthday_params[ent["entity"]] = [birthday_params[ent["entity"]], ent["value"]]

            if birthday_params.get("name"): details_parts.append(f"Имя/ФИО: '{birthday_params.get('name')}'")
            if birthday_specifiers: details_parts.append(f"Период (спецификатор): '{', '.join(birthday_specifiers)}'")
            if dates: details_parts.append(f"Период (дата): '{', '.join(dates)}'")
            if birthday_params.get("department"): details_parts.append(f"Отдел: '{birthday_params.get('department')}'")
            if birthday_params.get("project"): details_parts.append(f"Проект: '{birthday_params.get('project')}'")
            if birthday_params.get("age_older_than"): details_parts.append(
                f"Старше: '{birthday_params.get('age_older_than')}' лет")
            if birthday_params.get("age_younger_than"): details_parts.append(
                f"Младше: '{birthday_params.get('age_younger_than')}' лет")

            if "менеджер" in latest_message_text.lower(): details_parts.append(f"Должность (текст): 'менеджер'")
            if "удалён" in latest_message_text.lower(): details_parts.append(f"Статус (текст): 'удалённый'")

            if details_parts:
                response_message = f"✅ Запрос на поиск дней рождения принят. Критерии: {'; '.join(details_parts)}."
            else:
                response_message = "✅ Запрос на поиск дней рождения принят (без уточняющих критериев)."

        elif intent_name == "check_task":
            task_params = {"assignee": None}  # Default assignee to None
            dates = []
            task_tags = []
            for ent in extracted_data_for_backend["entities"]:
                if ent["entity"] == "name" and ent["value"].lower() in ["мои", "моя", "мое", "моё", "мне", "меня",
                                                                        "мной", "я"]:
                    task_params["assignee"] = "current_user"
                elif ent["entity"] == "date":
                    dates.append(ent["value"])
                elif ent["entity"] == "task_tag":
                    task_tags.append(ent["value"])
                elif ent["entity"] not in task_params:
                    task_params[ent["entity"]] = ent["value"]
                elif isinstance(task_params[ent["entity"]], list):
                    task_params[ent["entity"]].append(ent["value"])
                else:
                    task_params[ent["entity"]] = [task_params[ent["entity"]], ent["value"]]

            if task_params["assignee"] == "current_user":
                details_parts.append("Задачи для: 'текущего пользователя (мои)'")
            elif task_params.get("name"):
                details_parts.append(f"Исполнитель: '{task_params.get('name')}'")
            elif "assignee" not in task_params and not task_params.get("name") and \
                    any(keyword in latest_message_text.lower() for keyword in
                        ["мои ", "моя ", "моё ", "мне ", "меня ", "мной ", " я "]):
                details_parts.append("Задачи для: 'текущего пользователя (мои)'")

            if task_params.get("task_name"): details_parts.append(f"Название задачи: '{task_params.get('task_name')}'")
            if task_params.get("project"): details_parts.append(f"Проект: '{task_params.get('project')}'")
            if dates: details_parts.append(f"Дата/Дедлайн: '{', '.join(dates)}'")
            if task_params.get("task_status"): details_parts.append(f"Статус: '{task_params.get('task_status')}'")
            if task_params.get("task_priority"): details_parts.append(
                f"Приоритет: '{task_params.get('task_priority')}'")
            if task_tags: details_parts.append(f"Теги: '{', '.join(task_tags)}'")

            if "напоминания" in latest_message_text.lower() or "напомни" in latest_message_text.lower():
                details_parts.append("Тип: 'напоминание'")
            if "участник" in latest_message_text.lower(): details_parts.append("Роль: 'участник (из текста)'")
            if "согласования" in latest_message_text.lower() and "менеджера" in latest_message_text.lower():
                details_parts.append("Требуется: 'согласование менеджера (из текста)'")

            if details_parts:
                response_message = f"✅ Запрос на проверку задач принят. Критерии: {'; '.join(details_parts)}."
            else:
                response_message = "✅ Запрос на проверку задач принят (без уточняющих критериев)."

        elif intent_name == "check_employment_calendar":
            calendar_params = {"user": None}  # Default user to None
            dates = []

            for ent in extracted_data_for_backend["entities"]:
                if ent["entity"] == "name":
                    if ent["value"].lower() in ["мой", "моя", "моё", "моём", "мои", "меня", "мне", "мной", "я"]:
                        calendar_params["user"] = "current_user"
                    else:
                        calendar_params["user"] = ent["value"]
                elif ent["entity"] == "date":
                    dates.append(ent["value"])
                elif ent["entity"] not in calendar_params:
                    calendar_params[ent["entity"]] = ent["value"]
                elif isinstance(calendar_params[ent["entity"]], list):
                    calendar_params[ent["entity"]].append(ent["value"])
                else:
                    calendar_params[ent["entity"]] = [calendar_params[ent["entity"]], ent["value"]]

            if calendar_params["user"] == "current_user":
                details_parts.append("Календарь для: 'текущего пользователя (мой)'")
            elif calendar_params.get("user"):
                details_parts.append(f"Календарь для: '{calendar_params.get('user')}'")
            elif any(keyword in latest_message_text.lower() for keyword in
                     ["мой ", "моя ", "моё ", "моём ", "мои ", "меня ", "мне ", "мной ", " я "]):
                details_parts.append("Календарь для: 'текущего пользователя (мой)'")
            elif "календарь" in latest_message_text.lower() and not any(
                    e['entity'] == 'name' for e in extracted_data_for_backend["entities"]):
                details_parts.append("Календарь для: 'текущего пользователя (по умолчанию)'")

            if dates: details_parts.append(f"Период/Время: '{', '.join(dates)}'")
            if calendar_params.get("room_name"): details_parts.append(f"Ресурс: '{calendar_params.get('room_name')}'")
            if calendar_params.get("event_name"): details_parts.append(
                f"Тип события: '{calendar_params.get('event_name')}'")

            if "свободные слоты" in latest_message_text.lower() or \
                    "свободное время" in latest_message_text.lower() or \
                    "временные окна без встреч" in latest_message_text.lower():
                details_parts.append("Тип запроса: 'поиск свободных слотов'")
            elif "занятые часы" in latest_message_text.lower() or \
                    "загруженных дней" in latest_message_text.lower() or \
                    "загрузку" in latest_message_text.lower():
                details_parts.append("Тип запроса: 'поиск занятых слотов/загрузки'")
            elif "конфликты" in latest_message_text.lower():
                details_parts.append("Тип запроса: 'поиск конфликтов'")

            if "обеденный перерыв" in latest_message_text.lower() and not calendar_params.get("event_name"):
                details_parts.append("Тип события: 'обеденный перерыв'")

            if details_parts:
                response_message = f"✅ Запрос по календарю занятости принят. Критерии: {'; '.join(details_parts)}."
            else:
                response_message = "✅ Запрос по календарю занятости принят (без уточняющих критериев)."

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

        dispatcher.utter_message(text=response_message)
        return []