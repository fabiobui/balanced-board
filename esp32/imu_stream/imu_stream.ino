#include <Wire.h>
#include <MPU6050_tockn.h>

MPU6050 mpu6050(Wire);

void setup() {
  Serial.begin(115200);
  Wire.begin();

  mpu6050.begin();
  mpu6050.calcGyroOffsets(true);
}

void loop() {
  mpu6050.update();

  float pitch = mpu6050.getAngleX();
  float roll = mpu6050.getAngleY();

  // Formato: pitch,roll
  Serial.print(pitch, 2);
  Serial.print(",");
  Serial.println(roll, 2);

  delay(15);
}
