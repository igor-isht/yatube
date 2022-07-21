## Описание:

Блоu для публикации постов. Имеются возможности комментирования постов и подписок на любимых авторов

Доступен по адресу https://igor-prac.sytes.net/

Используемый стек: Django, Python, PostgreSQL, Nginx



### Как запустить проект на локальном компьютере:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/igor-isht/yatube.git
```

```
cd yatube
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env (MacOS, Linux)
python -m venv env (Windows)
```

```
source env/bin/activate (MacOS, Linux)
source env/Scripts/activate (Windows)
```

```
python3 -m pip install --upgrade pip
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
python manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
python manage.py runserver
```

Готово! Сервис досткпен по адресу http://127.0.0.1:8000/
