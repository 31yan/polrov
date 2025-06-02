#include <Wire.h>

#define BMI160_I2C_ADDRESS 0x68
#define ACCEL_SENSITIVITY 16384.0

// Variabel integrasi
float velocityX = 0, velocityY = 0, velocityZ = 0;
float displacementX = 0, displacementY = 0, displacementZ = 0;

const float dt = 0.1;  // 100 ms
const float alpha = 0.2;  // Koefisien filter low-pass (sesuaikan)

float ax_filtered = 0, ay_filtered = 0, az_filtered = 0;

void setup() {
  Serial.begin(9600);
  Wire.begin();

  Wire.beginTransmission(BMI160_I2C_ADDRESS);
  Wire.write(0x7E);
  Wire.write(0x11);
  Wire.endTransmission();
  delay(100);

  autoCalibrateAccelerometer();

  Serial.println("BMI160 Initialized and Calibrated");
}

void loop() {
  int16_t ax_raw, ay_raw, az_raw;

  Wire.beginTransmission(BMI160_I2C_ADDRESS);
  Wire.write(0x12);
  Wire.endTransmission(false);
  Wire.requestFrom(BMI160_I2C_ADDRESS, 6);

  if (Wire.available() == 6) {
    ax_raw = (int16_t)(Wire.read() | (Wire.read() << 8));
    ay_raw = (int16_t)(Wire.read() | (Wire.read() << 8));
    az_raw = (int16_t)(Wire.read() | (Wire.read() << 8));
  } else {
    Serial.println("Error reading accelerometer data");
    return;
  }

  float ax = ((float)ax_raw) * (9.81 / ACCEL_SENSITIVITY);
  float ay = ((float)ay_raw) * (9.81 / ACCEL_SENSITIVITY);
  float az = ((float)az_raw) * (9.81 / ACCEL_SENSITIVITY);

  // Filter low-pass (exponential moving average)
  ax_filtered = alpha * ax + (1 - alpha) * ax_filtered;
  ay_filtered = alpha * ay + (1 - alpha) * ay_filtered;
  az_filtered = alpha * az + (1 - alpha) * az_filtered;

  // Integrasi akselerasi terfilter
  velocityX += ax_filtered * dt;
  velocityY += ay_filtered * dt;
  velocityZ += az_filtered * dt;

  // Integrasi kecepatan
  displacementX += velocityX * dt;
  displacementY += velocityY * dt;
  displacementZ += velocityZ * dt;

  Serial.print("Accel filt (m/s^2): ");
  Serial.print(ax_filtered, 2); Serial.print(", ");
  Serial.print(ay_filtered, 2); Serial.print(", ");
  Serial.print(az_filtered, 2); Serial.println();

  Serial.print("Velocity (m/s): ");
  Serial.print(velocityX, 3); Serial.print(", ");
  Serial.print(velocityY, 3); Serial.print(", ");
  Serial.print(velocityZ, 3); Serial.println();

  Serial.print("Displacement (m): ");
  Serial.print(displacementX, 4); Serial.print(", ");
  Serial.print(displacementY, 4); Serial.print(", ");
  Serial.print(displacementZ, 4); Serial.println();

  Serial.println("-----------------------------");

  delay((int)(dt * 1000));
}

void autoCalibrateAccelerometer() {
  Wire.beginTransmission(BMI160_I2C_ADDRESS);
  Wire.write(0x7E);
  Wire.write(0x37);
  Wire.endTransmission();
  delay(1000);
  Serial.println("Accelerometer Auto-Calibration Complete");
}
