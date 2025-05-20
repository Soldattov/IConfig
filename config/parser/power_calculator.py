import re

def calculateGPUPower(gpu):
    """Рассчитывает потребляемую мощность видеокарты."""
    modifiers = {
            # Модификаторы (усиливают мощность)
            "SUPER": 1.03,
            "Ti": 1.02,
            "XT": 1.02,
            "XTX": 1.02,

            # Модели GPU (имеют фиксированный множитель)
            "RTX 5090": 3.2,
            "RTX 4090": 3.09,
            "RTX 5080": 3,
            "RTX 4080": 2.93,
            "RTX 5070": 2.76,
            "RTX 4070": 2.67,
            "RX 6900": 2.65,
            "RTX 3090": 2.62,
            "RTX 3080": 2.5,
            "RX 9070": 2.46,
            "RTX 5060":2.3,
            "RX 7700": 2.26,
            "RTX 3070": 2.22,
            "RX 6800": 2.19,
            "RTX 4060": 2,
            "RX 6700": 1.97,
            "RTX 2080": 1.95,
            "RTX 3060": 1.865,
            "RX 7600": 1.84,
            "RTX 2070": 1.817,
            "Arc B580": 1.793,
            "GTX 1080": 1.79,
            "RX 6600": 1.765,
            "RTX 4050": 1.73,
            "RX 5700": 1.727,
            "RX 2060": 1.716,
            "Arc B570": 1.697,
            "GTX 1070": 1.684,
            "Arc A770": 1.667,
            "GTX 1660": 1.59,
        }
    base_power = 100
    multiplier = 1.0  # Изначальный множитель

    if not gpu.model:
        gpu.relative_power = str(base_power)
        return

        # Проверяем все возможные модификаторы
    for keyword, mod in modifiers.items():
        if keyword in gpu.model:
            multiplier *= mod

        # Ограничиваем множитель разумными пределами (пока нет смысла)
        #multiplier = max(0.5, min(multiplier, 1.5))

    gpu.relative_power = str(int(base_power * multiplier))

def calculateCPUPower(cpu):
    """Рассчитывает потребляемую мощность процессора."""
    base_power = 100
    multiplier = 1.00

    modifiers = {
            # Модификаторы архитектур (базовые множители)
            "Intel Core i9": 1.4,
            "Intel Core i7": 1.2,
            "Intel Core i5": 1.05,
            "Intel Core i3": 0.8,
            "Intel Pentium": 0.6,
            "Intel Celeron": 0.5,
            "Ryzen 9": 1.4,
            "Ryzen 7": 1.2,
            "Ryzen 5": 1.05,
            "Ryzen 3": 0.8,

            # Поколения процессоров
            "14th Gen": 1.1,  # Intel
            "13th Gen": 1.05,
            "12th Gen": 1.0,
            "11th Gen": 0.95,
            "10th Gen": 0.9,
            "9xxx": 1.7,
            "7xxx": 1.4,  # AMD
            "5xxx": 1.1,
            "3xxx": 0.8,

            # Модификаторы моделей (например, "K", "X", "G")
            "K": 1.05,  # Разблокированный множитель (Intel)
            "KF": 1.05,
            "KS": 1.05,
            "X": 1.1,  # High-end (AMD)
            "X3D": 1.1,  # 3D V-Cache
            "G": 0.9,  # С графикой (менее мощный)
            "T":0.8,

            # Дополнительные модификаторы
            "Core": 1.1,
            "Ryzen": 1.2,
            "Threadripper": 2,  # AMD Threadripper
            "Xeon": 0.8,  # Intel Xeon
            "Athlon": 0.7,
            "A6":0.5,
            "A8":0.4,
        }

    if not cpu.model:
        cpu.relative_power = str(base_power)
        return

        #Проверяем поколение AMD и Intel
    if re.search(r"Ryzen [3579]\s*9\d{3}\w*", cpu.model):  # Примеры: Ryzen 9 7950X, Ryzen 9 5950X, Ryzen 9 3950X
        multiplier *= 1.7
    elif re.search(r"Ryzen [3579]\s*8\d{3}\w*", cpu.model):  # Примеры: Ryzen 3 7800X, Ryzen 3 5800X, Ryzen 3 3800
        multiplier *= 1.6
    if re.search(r"Ryzen [3579]\s*7\d{3}\w*", cpu.model):  # Примеры: Ryzen 7 7700X, Ryzen 7 5700X, Ryzen 7 3700
        multiplier *= 1.5
    elif re.search(r"Ryzen [3579]\s*6\d{3}\w*", cpu.model):  # Примеры: Ryzen 5 7600X, Ryzen 5 5600X, Ryzen 5 3600X
        multiplier *= 1.4
    elif re.search(r"Ryzen [3579]\s*5\d{3}\w*", cpu.model):  # Примеры: Ryzen 3 7500X, Ryzen 3 5500X, Ryzen 3 3500
        multiplier *= 1.3
    elif re.search(r"Ryzen [3579]\s*3\d{3}\w*", cpu.model):  # Примеры: Ryzen 3 7300X, Ryzen 3 5300X, Ryzen 3 3300X
        multiplier *= 1.2
        '''процессоры intel'''
    elif re.search(r"i[3579]-14\d{3}\w*", cpu.model):  # Примеры: i9-14900K, i7-14700K, i5-14600K
        multiplier *= 1.8
    elif re.search(r"i[3579]-13\d{3}\w*", cpu.model):  # Примеры: i9-13900K, i7-13700K, i5-13600K, i3-13100
        multiplier *= 1.7
    elif re.search(r"i[3579]-12\d{3}\w*", cpu.model):  # Примеры: i9-12900K, i7-12700K, i5-12600K, i3-12100
        multiplier *= 1.5
    elif re.search(r"i[3579]-11\d{3}\w*", cpu.model):  # Примеры: i9-11900K, i7-11700K, i5-11600K, i3-11100
        multiplier *= 1.3
    elif re.search(r"i[3579]-10\d{3}\w*", cpu.model):  # Примеры: i9-10900K, i7-10700K, i5-10600K, i3-10100
        multiplier *= 1.1
    elif re.search(r"i[3579]-9\d{3}\w*", cpu.model):  # Примеры: i9-9900K, i7-9700K, i5-9600K, i3-9100
        multiplier *= 0.9
    elif re.search(r"i[3579]-8\d{3}\w*", cpu.model):  # Примеры: i9-8950HK, i7-8700K, i5-8600K, i3-8100
        multiplier *= 0.7

        # Учитываем архитектуру и модель
    for keyword, mod in modifiers.items():
        if keyword in cpu.model:
            multiplier *= mod

        # Учитываем количество ядер и тактовую частоту (опционально)
    try:
        cores = int(cpu.cores_amount)
        if cores < 20:
            core_multiplier = 1 + (cores / 8) * 0.3  # +4% за каждое ядро после 8
        else:
            core_multiplier = 1
            multiplier *= core_multiplier
            base_freq = float(cpu.frequency.split()[0])  # "3.5 GHz" → 3.5
            freq_multiplier = 1 + (base_freq - 3.0) * 0.05  # +5% за каждые 0.1 ГГц выше 3.0
            multiplier *= freq_multiplier
    except (ValueError, TypeError):
        pass  # Если ядра/потоки не указаны

        # Ограничиваем множитель (может понадобится)
        #multiplier = max(0.5, min(multiplier, 2.0))  # От 0.5x до 2.0x

    cpu.relative_power = str(int(base_power * multiplier))
