# Минимальное веб-приложение для работы с сущностью «оборудование»
Тестовое задание от одной компании

## Настройка
1. Установка зависимостей:
    ```
    pip install -r requirements.txt
    ```
2. Импорт базы данных из дампа базы MySQL
    ```
    mysql -u [имя_нового_пользователя_бд] -p [имя_новой_бд] < db.sql
    ```
3. Настройка параметров в settings.ini
    По умолчанию они такие:
    ```
    [MySQL Database]
    name=equipement_project
    user=root
    password=root
    host=localhost
    port=3306
    [Other]
    page_size=10
    ```

## Запуск
   ```
   python manage.py runserver
   ```

## Логика
Приложение для backend использует Django, который на главной странице отображает SPA frontend сделанный на минимальном Vue.js. Для тестирования у админки пароль и логин admin, а в оборудовании уже занесены тестовые данные. Требование было сделать проект минимальным, а не production ready. Полагаю, это именно то, что вы хотели увидеть.

## Примеры запросов
Вход в аккаунт
```
POST /api/user/login/

Body:
{
    "password": "admin",
    "username": "admin"
}
```


Получение текущего списка серийных номеров с пагинацией и с фильтрацией
```
GET /api/equipment/?page=1&equipment_type__name=TP-Link+TL-WR74

Response:
{
    "count": 12,
    "next": "http://127.0.0.1:8000/api/equipment/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "equipment_type": {
                "id": 1,
                "name": "TP-Link TL-WR74",
                "serial_number_mask": "XXAAAAAXAA"
            },
            "serial_number": "1AABCDE9BC",
            "note": "Тестовый роутер 1",
            "is_deleted": false
        },
        {
            "id": 3,
            "equipment_type": {
                "id": 1,
                "name": "TP-Link TL-WR74",
                "serial_number_mask": "XXAAAAAXAA"
            },
            "serial_number": "2AABCDE9BC",
            "note": "123",
            "is_deleted": false
        },
        {
            "id": 4,
            "equipment_type": {
                "id": 1,
                "name": "TP-Link TL-WR74",
                "serial_number_mask": "XXAAAAAXAA"
            },
            "serial_number": "1AABCDE9BD",
            "note": "aaaaa",
            "is_deleted": false
        }...
    ]
}
```


Создание новой(ых) записи(ей) оборудования.
```
POST /api/equipment/

Body:
{
    "equipment_type_id": 1,
    "serial_numbers": ["SN001", "SN002", "SN003"],
    "note": "Test batch"
}
```
