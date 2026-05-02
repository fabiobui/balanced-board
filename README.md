# Balanced Board Trainer

Semplice prototipo per allenamento su pedana con ESP32 + IMU.

## Cosa fa
- Visualizza una traiettoria sinusoidale che scorre da sinistra verso destra.
- Mostra la posizione della pedana (punto controllato dall'IMU).
- Evidenzia se il punto resta dentro una banda di tolleranza attorno alla sinusoide.
- Calcola una percentuale di accuratezza durante la sessione.

## Struttura
- `app/main.py`: applicazione desktop (Python + Pygame).
- `esp32/imu_stream/imu_stream.ino`: firmware ESP32 (MPU6050) che invia `pitch,roll` via seriale.

## Requisiti PC
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Esecuzione
Senza sensore (simulazione tastiera):
```bash
python app/main.py --mode keyboard
```

Con ESP32 su seriale:
```bash
python app/main.py --mode serial --port /dev/ttyUSB0 --baud 115200
```

## Controlli modalità keyboard
- Frecce direzionali: muovi il punto.
- `R`: reset punteggio.
- `ESC`: esci.

## Note di calibrazione
- Il firmware invia valori in gradi. L'app normalizza automaticamente su una finestra [-20°, +20°].
- Per pedane molto sensibili puoi aumentare `--tolerance` o ridurre `--amplitude`.
