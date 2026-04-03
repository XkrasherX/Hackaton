# ⚡ Швидкий Старт

## За 2 Хвилини

### 1. Встановити
```bash
pip install -r requirements.txt
```

### 2. Запустити Веб-Додаток
```bash
streamlit run app/core/app.py
```

### 3. Завантажити Лог
1. Браузер відкриється на http://localhost:8501
2. Перетягніть файл `.BIN` або `.LOG` в область завантаження
3. Система автоматично обчислить метрики та покаже траєкторію

## Графіки Показуються

- 📊 **Метрики**: Дистанція, швидкість, прискорення
- 🛤️ **3D Траєкторія**: Інтерактивна карта маршруту
- 📈 **Графіки**: Висота, горизонтальна та вертикальна швидкість

## AI Аналіз (Опціональний)

### Без API Ключа
Система автоматично використовує правила для:
- Виявлення аномалій (швидкість, висота)
- Генерування рекомендацій
- Текстового звіту

### З Groq API Ключем
Для краще якості аналізу:

1. Реєстрація: https://console.groq.com/
2. Скопіюйте API ключ (безкоштовний, без карти)
3. Введіть в Streamlit ("Settings" в лівій панелі)
4. Отримайте експерт-рівень аналіз від Mixtral AI

## Файли для Тестування

Проект включає приклади:
- `data/00000001.BIN` - Прямий або звичайний польот
- `data/00000019.BIN` - Додатковий приклад

## Python Код

### Прошальний Аналіз
```python
from app.core import parse_ardupilot_log

gps_df, imu_df = parse_ardupilot_log("data/00000001.BIN")
print(f"GPS точок: {len(gps_df)}, IMU точок: {len(imu_df)}")
```

### З AI Аналізом
```python
from app.core import parse_ardupilot_log, analyze_flight_with_ai

gps_df, imu_df = parse_ardupilot_log("data/00000001.BIN")

analysis = analyze_flight_with_ai({...}, gps_df, imu_df)
print(analysis['summary'])
print(analysis['recommendations'])
```

Див. `example.py` для повного прикладу.

## Моделі

| Компонент | Тип | Опис |
|-----------|-----|------|
| **Парсинг** | Binary | ArduPilot BIN/LOG формати |
| **Координати** | WGS-84 → ENU | GPS трансформація |
| **Метрики** | Haversine | Дистанція з точністю ±0.5% |
| **Орієнтація** | Quaternion | Без gimbal lock |
| **AI** | Mixtral-8x7B | Free tier, 30 req/min |
| **Резервний** | Rule-based | Без API, ~80% точності |

## Структура Проекту

```
app/
├── main.py           # CLI версія
└── core/
    ├── app.py        # Streamlit додаток
    ├── parser.py     # Парсинг logів
    ├── metrics.py    # Обчислення
    ├── coordinates.py # Трансформації
    ├── theory.py     # Математика
    ├── ai_analysis.py # AI модель
    └── ...
```

## Документація

- **[README.md](README.md)** - Повний опис
- **[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)** - Нові можливості
- **[INSTALL.md](INSTALL.md)** - Деталі встановлення
- **[app/core/theory.py](app/theory.py)** - Математичні основи

## Проблеми Та Рішення

### Streamlit не запускається
```bash
pip install --upgrade streamlit
```

### API помилка
Система автоматично переходить на резервний режим. Впізнай в логох "Fallback analysis".

### Неправильні координати
Переконайтеся, що файл BIN містить GPS дані. Перевірте в консолі кількість GPS точок.

## Наступні Кроки

1. ✅ Запустіть Streamlit
2. 🚀 Завантажте свій лог
3. 📊 Переглядайте метрики та графіки
4. 🤖 Опціонально: Додайте API 
5. 📤 Експортуйте дані

**Готово!** Система готова до використання.

---

Див. `INSTALL.md` для більш детальних інструкцій встановлення.
