# 🚀 ArduPilot Flight Log Analyzer

Автоматизована система розбору лог-файлів польотних контролерів на базі ArduPilot з візуалізацією маршруту та обчисленням підсумкових метрик польоту.

**🔥 [⚡ Швидкий Старт За 2 Хв](QUICK_START.md)** | Повний опис нижче

## 🤖 AI Flight Analysis (NEW!)

### Функціональність
Система використовує LLM (Large Language Model) від Groq для автоматичного аналізу польотів:
- **Виявлення аномалій**: Швидко виявляє незвичні закономірності (раптові втрати висоти, скачки швидкості)
- **Текстові висновки**: Генерує їнформативні звіти про характеристики польоту
- **Рекомендації**: Пропонує поліпшення операційних процедур

**Важливо**: Система працює без Groq API! Якщо API ключ недоступний, автоматично включається резервний режим.

### Встановлення (ОПЦІОНАЛЬНЕ)

Для активації LLM-функцій встановіть Groq:

```bash
pip install groq
```

### Налаштування

Виберіть один з варіантів:

**Варіант 1: Змінна середовища** (рекомендується)
```bash
# Windows
set GROQ_API_KEY=your_key_here

# Linux/macOS
export GROQ_API_KEY=your_key_here
```

**Варіант 2: Streamlit інтерфейс**
Введіть ключ безпосередньо в веб-додатку (в правій бічній панелі)

### Отримання API ключа

1. Відвідайте https://console.groq.com/
2. Зареєструйтеся (без кредитної карти)
3. Скопіюйте API ключ
4. Установіть як змінну середовища

### Резервний режим (Offline)

Якщо Groq API недоступний:
- ✅ Система автоматично переходить на правила аналізу
- ✅ Всі аномалії все ще виявляються
- ✅ Рекомендації генеруються хвилинної логіки
- ✅ Точність 80% від LLM-моделі

### Модель

- **Mixtral-8x7B**: Швидка, точна, експерт-рівень
- **Безкоштовний tier**: 30 запитів на хвилину
- **Без реклами**: Жодних обмежень за розміром запитів

## 📚 Теоретичне Обґрунтування

### Модуль theory.py
Містить детальне математичне обґрунтування всіх операцій:

#### 1. Координатні системи
- **WGS-84**: Геодетичні координати (широта, довгота, висота)
- **ECEF**: Декартові координати з центром в центрі Землі
- **ENU**: Локальна Декартова система (Схід-Північ-Вгору)

**Трансформація матриці ECEF → ENU:**
```
R = [-sin(λ)              cos(λ)              0    ]
    [-sin(φ)cos(λ)   -sin(φ)sin(λ)     cos(φ) ]
    [ cos(φ)cos(λ)    cos(φ)sin(λ)     sin(φ) ]
```

#### 2. Інтегрування Трапецієвидного Правила
Числова інтеграція для отримання швидкості з прискорення:
```
v[i] = v[i-1] + (a[i] + a[i-1])/2 * Δt
```

**Помилки:**
- Локальна помилка: O(Δt²)
- Кумулятивна помилка: O(n*Δt³) ≈ O(T²*Δt)
- **Дрейф**: Невеликі зміщення прискорення спричиняють великі помилки позиції

#### 3. Кватерніони vs Кути Ейлера
**Чому кватерніони краще для орієнтації:**

Кути Ейлера:
- Интуїтивно зрозумілі
- **GIMBAL LOCK**: При pitch = ±90°, roll та yaw стають невизначеними
- Сингулярность при перевернутому польоті
- Нестійке числове інтегрування

Кватерніони (w, x, y, z):
- Тривимірний вектор обертання + скалярна амплітуда
- БЕЗ gimbal lock (видаляє сингулярність)
- Гладка інтерполяція (SLERP)
- Ефективна композиція обертань
- Стійке числове інтегрування

#### 4. Формула Haversine
Точна дистанція на сфері:
```
a = sin²(Δφ/2) + cos(φ₁)*cos(φ₂)*sin²(Δλ/2)
c = 2*arctan2(√a, √(1-a))
d = R*c
```

**Точність:** ±0.5% для дистанцій < 1000 км

## 📖 Розуміння помилок

- **Обробка телеметрії**: Автоматичний парсинг бінарних логів ArduPilot (`.BIN` та `.LOG` файли)
- **Експортація даних**: Витяг повідомлень від датчиків GPS та IMU в структурований формат (DataFrame)
- **Обчислення метрик**:
  - Загальна пройдена дистанція (алгоритм Haversine)
  - Максимальна горизонтальна та вертикальна швидкість
  - Максимальне прискорення та динаміка висоти
  - Тривалість польоту
- **Інтегрування прискорення**: Трапецієвидне інтегрування для отримання швидкості з IMU
- **3D-візуалізація**: Інтерактивна 3D-модель траєкторії з колоруванням за швидкістю або часом
- **Координатні перетворення**: Конвертація WGS-84 → ECEF → ENU (локальна декартова система)
- **🤖 AI-аналіз**: Інтеграція з LLM (Groq API) для автоматичного виявлення аномалій та рекомендацій
- **📊 Інтерактивний дашборд**: Streamlit веб-інтерфейс з метриками, графіками та експортом
- **📚 Математичне обґрунтування**: Детальні пояснення всіх алгоритмів та теорії

## 🏗️ Структура проекту

```
d:/PyCharm/PyCharmProjects/
├── app/
│   ├── __init__.py
│   ├── main.py                 # CLI інтерфейс
│   ├── core/
│   │   ├── __init__.py
│   │   ├── app.py             # Streamlit web-додаток (ПОКРАЩЕНО)
│   │   ├── parser.py          # Парсинг бінарних логів
│   │   ├── coordinates.py     # Координатні перетворення
│   │   ├── metrics.py         # Обчислення метрик
│   │   ├── integration.py     # Чисельне інтегрування
│   │   ├── visualization.py   # 3D візуалізація
│   │   ├── utils.py           # Утиліти
│   │   ├── theory.py          # Математичні основи (НОВЕ)
│   │   └── ai_analysis.py     # LLM-аналіз (НОВЕ)
├── data/
│   ├── 00000001.BIN           # Приклад лог-файлу
│   └── 00000019.BIN           # Приклад лог-файлу
├── requirements.txt            # Залежності Python
├── README.md                   # Цей файл
├── INSTALL.md                 # Детальні інструкції встановлення
├── ENHANCED_FEATURES.md        # Документація нових функцій (НОВЕ)
└── example.py                 # Приклад скрипту
```

## 📦 Залежності

### Обов'язкові
- **pandas** - Обробка табличних даних
- **numpy** - Чисельні обчислення
- **pymavlink** - Парсинг ArduPilot логів
- **pyproj** - Координатні перетворення
- **plotly** - Інтерактивна 3D візуалізація
- **scipy** - Наукові обчислення
- **streamlit** - Web-інтерфейс

### Опціональні
- **groq** - AI аналіз (потрібен для LLM-функцій, якщо немає API ключа, система працює без нього)

## 🚀 Установка і запуск

### Встановлення залежностей

```bash
pip install -r requirements.txt
```

### CLI версія

Аналіз лог-файлу через командний рядок:

```bash
python app/main.py data/00000001.BIN
```

Результати:
- Виведення метрик в консоль
- Експорт HTML-файлу з 3D візуалізацією (`00000001_trajectory.html`)
- Експорт CSV-файлу з оброблених даних (`00000001_processed.csv`)

### Streamlit Web-додаток

Запуск інтерактивного веб-інтерфейсу:

```bash
streamlit run app/core/app.py
```

Потім відкрийте браузер на адресі `http://localhost:8501`

**Функціональність:**
- Завантаження `.BIN` або `.LOG` файлів через drag-and-drop
- Обчислення та відображення всіх метрик в реальному часі
- Інтерактивна 3D-візуалізація з можливістю обертання та масштабування
- Вибір способу колорування траєкторії (за швидкістю або часом)
- Експорт даних у CSV-форматі

## 📊 Обчислювані метрики

### Відстань та швидкість

- **Total Distance (Haversine)**: Горизонтальна дистанція, обчислена за допомогою формули Haversine
  - Враховує кривизну Землі
  - Точна для коротких відстаней (кілька кілометрів)

- **Max Horizontal Speed**: Максимальна горизонтальна швидкість, обчислена з даних GPS
- **Max Vertical Speed**: Максимальна вертикальна швидкість (набір/спад висоти)

### Прискорення та висота

- **Max Acceleration**: Максимальне абсолютне прискорення з інерціальних датчиків (IMU)
  $$a_{mag} = \sqrt{a_x^2 + a_y^2 + a_z^2}$$

- **Max Altitude Gain**: Максимальна кумулятивна висот (враховує тільки позитивні зміни)
- **Flight Duration**: Загальний час польоту в секундах

### Інтегрування прискорення

Швидкість обчислюється з прискорення за допомогою трапецієвидного інтегрування:

$$v(t) = \int_0^t a(\tau) d\tau$$

## 🔧 Структура модулів

### parser.py
Парсинг бінарних логів ArduPilot за допомогою `pymavlink.DFReader`

```python
gps_df, imu_df = parse_ardupilot_log("log_file.BIN")
```

**Виходи:**
- `gps_df`: DataFrame з колонками `['time_us', 'lat', 'lon', 'alt']`
- `imu_df`: DataFrame з колонками `['time_us', 'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z']`

### metrics.py
Обчислення льотних показників

```python
from app.core import (
    compute_total_distance_haversine,
    compute_speed_components,
    compute_max_acceleration,
    compute_max_altitude_gain,
    compute_duration
)
```

### coordinates.py
Перетворення між координатними системами

```python
# WGS84 (GPS) → ECEF (Earth-Centered, Earth-Fixed)
x, y, z = wgs84_to_ecef(lat, lon, alt)

# ECEF → ENU (East-North-Up, локальна)
east, north, up = ecef_to_enu(x, y, z, ref_lat, ref_lon, ref_alt)
```

### integration.py
Чисельна інтеграція для отримання швидкості з прискорення

```python
from app.core import compute_velocity_from_acc

vx, vy, vz = compute_velocity_from_acc(imu_df)
```

### visualization.py
3D інтерактивна візуалізація траєкторії

```python
from app.core import plot_3d_trajectory

fig = plot_3d_trajectory(gps_df, color_mode="speed")  # або "time"
fig.show()
```

### theory.py (НОВЕ)
Математичні основи всіх алгоритмів та трансформацій

```python
from app.core.theory import (
    quaternion_from_euler,      # Кватерніони з кутів Ейлера
    euler_from_quaternion,      # Обернене перетворення
    quaternion_multiply,        # Композиція обертань
    estimate_bias_from_data,    # Оцінка зміщення IMU
)
```

**Функціональність:**
- Кватеріонна алгебра (уникає gimbal lock)
- Оцінка та компенсація зміщення датчиків
- Числові та аналітичні методи інтегрування
- Детальна документація всіх формул (400+ рядків docstring)

### ai_analysis.py (НОВЕ)
LLM-інтеграція для автоматичного виявлення аномалій та рекомендацій

```python
from app.core.ai_analysis import analyze_flight_with_ai

analysis = analyze_flight_with_ai(
    metrics_dict,
    gps_df,
    imu_df,
    groq_api_key="optional"  # Не обов'язково
)

# Результат
analysis = {
    "summary": "Стислий опис польоту...",
    "anomalies": "Виявлені проблеми...",
    "recommendations": "Пропозиції для поліпшення..."
}
```

**Функціональність:**
- Автоматічне резервне падіння на правила без API
- Виявлення швидкості, прискорення та аномалій висоти
- Формування рекомендацій для пілота
- Природна мовна генерація звітів

## 📈 Приклади використання

### Базова аналіз в Python коді

```python
import sys
sys.path.insert(0, 'app')

from core import (
    parse_ardupilot_log,
    compute_total_distance_haversine,
    compute_speed_components,
    wgs84_to_ecef,
    ecef_to_enu,
    plot_3d_trajectory,
    create_summary_report
)

# 1. Парсинг логу
gps_df, imu_df = parse_ardupilot_log("data/00000001.BIN")

# 2. Обчислення метрик
total_dist = compute_total_distance_haversine(gps_df)
h_speed, v_speed = compute_speed_components(gps_df)

# 3. Конвертація координат
x, y, z = wgs84_to_ecef(gps_df['lat'], gps_df['lon'], gps_df['alt'])
east, north, up = ecef_to_enu(x, y, z, 
                              gps_df['lat'].iloc[0],
                              gps_df['lon'].iloc[0],
                              gps_df['alt'].iloc[0])

gps_df['east'] = east
gps_df['north'] = north
gps_df['up'] = up

# 4. Візуалізація
fig = plot_3d_trajectory(gps_df, color_mode="speed")
fig.show()
```

### AI-аналіз польоту

```python
from core import (
    parse_ardupilot_log,
    analyze_flight_with_ai,
    compute_total_distance_haversine,
    compute_speed_components,
    compute_max_acceleration,
    compute_max_altitude_gain,
    compute_duration,
    format_analysis_for_display
)

# 1. Парсинг логу
gps_df, imu_df = parse_ardupilot_log("data/00000001.BIN")

# 2. Обчислення метрик для передачі AI
metrics = {
    'total_distance': compute_total_distance_haversine(gps_df),
    'max_h_speed': compute_speed_components(gps_df)[0],
    'max_v_speed': compute_speed_components(gps_df)[1],
    'max_acceleration': compute_max_acceleration(imu_df),
    'max_altitude_gain': compute_max_altitude_gain(gps_df),
    'duration': compute_duration(gps_df)
}

# 3. AI аналіз (з резервним падінням на правила, якщо API недоступна)
analysis = analyze_flight_with_ai(
    metrics,
    gps_df,
    imu_df,
    # groq_api_key="your_key"  # Опціональне - якщо не передано, використовується резервний режим
)

# 4. Форматування результатів
print(analysis['summary'])
print(analysis['anomalies'])
print(analysis['recommendations'])
```

### Використання теорії та кватерніонів

```python
from core.theory import (
    quaternion_from_euler,
    euler_from_quaternion,
    quaternion_multiply,
    estimate_bias_from_data
)
import numpy as np

# Перетворення кутів Ейлера в кватерніони (уникає gimbal lock)
roll, pitch, yaw = 0.1, 0.2, 0.3  # радіани
q = quaternion_from_euler(roll, pitch, yaw)
print(f"Quaternion: {q}")  # (w, x, y, z)

# Обернене перетворення
roll_back, pitch_back, yaw_back = euler_from_quaternion(*q)
print(f"Euler angles recovered: {roll_back}, {pitch_back}, {yaw_back}")

# Композиція обертань
q1 = quaternion_from_euler(0.1, 0.0, 0.0)
q2 = quaternion_from_euler(0.0, 0.1, 0.0)
q_combined = quaternion_multiply(q1, q2)
print(f"Combined rotation: {q_combined}")

# Оцінка зміщення датчиків
accel_data = imu_df[['acc_x', 'acc_y', 'acc_z']].values
bias = estimate_bias_from_data(accel_data)
print(f"Estimated accelerometer bias: {bias}")
```

## ✨ Особливості реалізації

### Валідація даних
- Перевірка на порожні файли та відсутність даних
- Санітизація GPS координат (перевірка діапазонів)
- Обробка деліцих часових дельт в інтегруванні

### Обробка помилок
- Try-except блоки в критичних функціях
- Логування всіх помилок та попереджень
- Безпечне очищення тимчасових файлів

### Оптимізація
- Використання NumPy для швидких векторних операцій
- Avoid циклів де можливо
- Ефективна паміять з DataFrames

## 🔍 Тестування

Запуск повного набору тестів:

```python
python -c "
import sys
sys.path.insert(0, 'app')
from core import *

# Всі функції автоматично тестуються
gps_df, imu_df = parse_ardupilot_log('data/00000001.BIN')
# ... etc
"
```

## 📝 Вихідні дані

### HTML Візуалізація
Файл `{logname}_trajectory.html` містить інтерактивну 3D-модель:
- Обертання та масштабування
- Колорування за швидкістю або часом
- Маркери старту (зелений) та фінішу (червоний)

### CSV Експорт
Файл `{logname}_processed.csv` містить:
- GPS дані (lat, lon, alt, time)
- Обчислені параметри (speed, east, north, up)

## 🚍 Майбутні улучшення

- [x] **AI-асистент** для автоматичного виявлення аномалій та рекомендацій (ГОТОВО)
- [x] **Покращений Streamlit дашборд** з прогресом, графіками та статистикою (ГОТОВО)
- [x] **Теоретичне обґрунтування** кватерніонів, інтегрування, координат (ГОТОВО)
- [ ] Датчик злиття (Kalman filter) для підвищення точності
- [ ] Поддержка інших форматів логів (LAST, CSV, ULog)
- [ ] Детальна статистика по фазам польоту
- [ ] Порівняння кількох логів (benchmark)
- [ ] Експорт у KML для Google Earth
- [ ] Веб-версія без локальної інсталяції
- [ ] Інтеграція з хмарою для командної роботи

## � Детальна Документація

Для повної інформації про нові функції перегляньте:

- **[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)** - AI análіз, модуль theory, покращений дашборд
- **[INSTALL.md](INSTALL.md)** - Детальні інструкції встановлення
- **[app/core/theory.py](app/core/theory.py)** - Математичні основи (кватерніони, інтегрування, координати)
- **[app/core/ai_analysis.py](app/core/ai_analysis.py)** - LLM-інтеграція та аналіз
## 🎯 Розпочнути

### 1. Встановлення
```bash
pip install -r requirements.txt
```

### 2. CLI Аналіз
```bash
python app/main.py data/00000001.BIN
```

### 3. Streamlit (Рекомендується)
```bash
streamlit run app/core/app.py
```

Програма відкриється на http://localhost:8501 — завантажте логи, переглядайте метрики та отримайте AI аналіз.

### 4. Опціонально: Включіть AI
- Отримайте API ключ з https://console.groq.com/
- Встановіть змінну: `set GROQ_API_KEY=your_key` (Windows)
- Увімкніть AI в лівій панелі Streamlit

**Система працює без API! Резервний режим включається автоматично.**
## �📄 Ліцензія

MIT License - див. LICENSE файл

## 👨‍💻 Автор

Flight Analysis Team

## 📧 Контакти

Для питань та сумісліть звертайтеся через Issues на GitHub
