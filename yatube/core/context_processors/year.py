from datetime import date


def year(today):
    """Добавляет переменную с текущим годом."""
    today = date.today()
    year_today = today.year
    return {
        'year': year_today
    }
