#include <Wire.h>
#include <Adafruit_BNO08x.h>

// D1 mini ESP32 default I2C pins
static const int I2C_SDA = 21;
static const int I2C_SCL = 22;

Adafruit_BNO08x bno08x(-1); // reset pin non usato
sh2_SensorValue_t sensorValue;

bool enableReports() {
  // Rotation Vector: quaternione assoluto, stabile per orientamento
  return bno08x.enableReport(SH2_ROTATION_VECTOR, 20000); // 20ms = 50Hz
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(I2C_SDA, I2C_SCL);
  Wire.setClock(400000);

  if (!bno08x.begin_I2C(0x4B, &Wire)) {
    Serial.println("ERR:BNO085_NOT_FOUND");
    while (true) {
      delay(500);
    }
  }

  if (!enableReports()) {
    Serial.println("ERR:REPORT_ENABLE_FAILED");
    while (true) {
      delay(500);
    }
  }

  Serial.println("OK:BNO085_READY");
}

void loop() {
  if (bno08x.getSensorEvent(&sensorValue)) {
    if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {
      float qw = sensorValue.un.rotationVector.real;
      float qx = sensorValue.un.rotationVector.i;
      float qy = sensorValue.un.rotationVector.j;
      float qz = sensorValue.un.rotationVector.k;

      // Quaternion -> Euler (roll/pitch in gradi)
      float sinr_cosp = 2.0f * (qw * qx + qy * qz);
      float cosr_cosp = 1.0f - 2.0f * (qx * qx + qy * qy);
      float roll = atan2f(sinr_cosp, cosr_cosp);

      float sinp = 2.0f * (qw * qy - qz * qx);
      float pitch;
      if (fabsf(sinp) >= 1.0f) {
        pitch = copysignf(PI / 2.0f, sinp);
      } else {
        pitch = asinf(sinp);
      }

      float pitchDeg = pitch * 180.0f / PI;
      float rollDeg = roll * 180.0f / PI;

      // Formato compatibile con app Python: pitch,roll
      Serial.print(pitchDeg, 2);
      Serial.print(",");
      Serial.println(rollDeg, 2);
    }
  }
}
