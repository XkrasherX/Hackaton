import pandas as pd
from pymavlink import mavutil

def calculate_sampling_rate(timestamps: pd.Series) -> float:
    """Обчислює середню частоту семплювання (Hz) на основі часових міток."""
    if len(timestamps) < 2:
        return 0.0
    duration = timestamps.max() - timestamps.min()
    if duration <= 0:
        return 0.0
    return round(len(timestamps) / duration, 2)

def parse_ardupilot_log(file_path: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """  Витягує повідомлення GPS та IMU з бінарного логу. """
    try:
        # pymavlink для роботи з сирими .bin файлами Ardupilot
        mlog = mavutil.mavlink_connection(file_path)
    except Exception as e:
        raise ValueError(f"Помилка відкриття файлу логу: {e}")

    gps_data = []
    imu_data = []

    while True:
        # blocking=False для швидкого читання вже наявного файлу
        msg = mlog.recv_match(type=['GPS', 'IMU'], blocking=False)
        if msg is None:
            break

        msg_type = msg.get_type()
        # Безпечне отримання часу. Якщо його немає - пропускаємо битий пакет
        timestamp = getattr(msg, '_timestamp', None)
        if timestamp is None:
            continue

        if msg_type == 'GPS':
            gps_data.append({
                'Time': timestamp,
                # Ardupilot зберігає координати у форматі цілих чисел (помножених на 1e7)
                'Lat': getattr(msg, 'Lat', 0) / 1e7,  
                'Lng': getattr(msg, 'Lng', 0) / 1e7,
                'Alt': getattr(msg, 'Alt', 0)
            })
        elif msg_type == 'IMU':
            imu_data.append({
                'Time': timestamp,
                'AccX': getattr(msg, 'AccX', 0),
                'AccY': getattr(msg, 'AccY', 0),
                'AccZ': getattr(msg, 'AccZ', 0)
            })

    df_gps = pd.DataFrame(gps_data)
    df_imu = pd.DataFrame(imu_data)

    if df_gps.empty or df_imu.empty:
         raise ValueError("Лог-файл не містить достатньо даних GPS або IMU. Перевірте формат.")

    # Формування метаданих датчиків
    metadata = {
        "GPS": {
            "sampling_rate_hz": calculate_sampling_rate(df_gps['Time']),
            "units": {"Lat": "градуси", "Lng": "градуси", "Alt": "метри"}
        },
        "IMU": {
            "sampling_rate_hz": calculate_sampling_rate(df_imu['Time']),
            "units": {"AccX": "м/с²", "AccY": "м/с²", "AccZ": "м/с²"}
        }
    }

    return df_gps, df_imu, metadata