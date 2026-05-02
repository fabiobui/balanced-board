# Balanced Board Trainer

Semplice prototipo per allenamento su pedana con ESP32 + IMU.

## Cosa fa
- Visualizza una traiettoria di allenamento, con scenari practice, intermediate o advanced.
- Mostra la posizione della pedana (punto controllato dall'IMU).
- Evidenzia se il punto resta dentro una banda di tolleranza attorno al percorso.
- Calcola una percentuale di accuratezza durante la sessione.

## Scenari
- `practice`: mantiene la sinusoide classica, utile per prendere confidenza con il movimento alto/basso.
- `intermediate`: mantiene il movimento verticale come `practice`, ma cambia in modo irregolare ampiezza e lunghezza d'onda della sinusoide.
- `advanced`: usa un percorso 2D irregolare con variazioni anche a destra e sinistra, così l'allenamento richiede correzioni su entrambi gli assi.

## Hardware aggiornato
- MCU: **D1 mini ESP32**
- Sensore IMU: **BNO085** (I2C)

## Schema elettrico collegamenti (I2C)
Collega il BNO085 al D1 mini ESP32 così:

- **BNO085 VIN / 3V3** → **ESP32 3V3**
- **BNO085 GND** → **ESP32 GND**
- **BNO085 SDA** → **ESP32 GPIO21 (SDA)**
- **BNO085 SCL** → **ESP32 GPIO22 (SCL)**

Opzionali (non necessari per questo firmware):
- **BNO085 INT** → non collegato
- **BNO085 RST** → non collegato
- **BNO085 PS0/PS1**: lasciare configurazione I2C del breakout (default)

> Nota: se il tuo breakout BNO085 espone solo alimentazione a 3.3V, NON usare 5V.

## Parametri configurabili
Puoi impostare direttamente da riga comando:
- `--scenario`: `practice`, `intermediate` oppure `advanced`.
- `--speed`: velocità di scorrimento della traiettoria.
- `--amplitude`: ampiezza generale del movimento.
- `--tolerance`: ampiezza della banda di tolleranza.
- `--wavelength`: larghezza base dell'onda/percorso.

Inoltre durante l'esecuzione puoi modificarli live:
- `TAB`: passa ciclicamente tra `practice`, `intermediate` e `advanced`.
- `1/2`: diminuisci/aumenta velocità.
- `3/4`: diminuisci/aumenta ampiezza.
- `5/6`: diminuisci/aumenta tolleranza.
- `7/8`: diminuisci/aumenta larghezza del percorso.

## Struttura
- `app/main.py`: applicazione desktop (Python + Pygame).
- `esp32/imu_stream/imu_stream.ino`: firmware ESP32 con BNO085 che invia `pitch,roll` via seriale.

## Requisiti PC
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Esecuzione
Senza sensore (simulazione tastiera):
```bash
python app/main.py --mode keyboard --scenario advanced --speed 250 --amplitude 120 --tolerance 35 --wavelength 650
```

Per una prova intermedia:
```bash
python app/main.py --mode keyboard --scenario intermediate --speed 220 --amplitude 250 --tolerance 65 --wavelength 700
```

Con ESP32 su seriale:
```bash
python app/main.py --mode serial --scenario advanced --port /dev/ttyUSB0 --baud 115200 --speed 250 --amplitude 120 --tolerance 35 --wavelength 650

python app/main.py --mode serial --scenario practice --port /dev/ttyUSB0 --baud 115200 --speed 150 --amplitude 160 --tolerance 70 --wavelength 650

```

## Controlli modalità keyboard
- Frecce direzionali: muovi il punto.
- `R`: reset punteggio.
- `TAB`: cambia scenario.
- `ESC`: esci.

## Note di calibrazione
- Il firmware invia valori in gradi nel formato `pitch,roll`.
- L'app normalizza automaticamente su una finestra [-20°, +20°].
- Per pedane molto sensibili puoi aumentare `--tolerance` o ridurre `--amplitude`.


### Seriale su Windows in WSL

Con PowerShell con privilegi da Amministratore

```
usbipd list
usbipd bind --busid 6-2
usbipd attach --wsl --busid 6-2
```

in Wsl per verificare

```
screen /dev/ttyUSB0 115200
```

CTRL+a + k per fermare

