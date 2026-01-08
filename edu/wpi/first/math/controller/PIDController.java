package edu.wpi.first.math.controller;

public class PIDController {
  private final double kP;
  private final double kI;
  private final double kD;
  private boolean continuous = false;
  private double minInput = -Math.PI;
  private double maxInput = Math.PI;

  public PIDController(double kP, double kI, double kD) {
    this.kP = kP;
    this.kI = kI;
    this.kD = kD;
  }

  public void enableContinuousInput(double minInput, double maxInput) {
    this.continuous = true;
    this.minInput = minInput;
    this.maxInput = maxInput;
  }

  public double calculate(double measurement, double setpoint) {
    double error = setpoint - measurement;
    if (continuous) {
      double range = maxInput - minInput;
      while (error > Math.PI) {
        error -= range;
      }
      while (error < -Math.PI) {
        error += range;
      }
    }
    return kP * error + kI * 0 + kD * 0;
  }
}
