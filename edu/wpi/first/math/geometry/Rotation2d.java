package edu.wpi.first.math.geometry;

public class Rotation2d {
  private final double radians;

  public Rotation2d() {
    this(0.0);
  }

  public Rotation2d(double radians) {
    this.radians = radians;
  }

  public static Rotation2d fromRadians(double radians) {
    return new Rotation2d(radians);
  }

  public static Rotation2d fromDegrees(double degrees) {
    return new Rotation2d(Math.toRadians(degrees));
  }

  public double getRadians() {
    return radians;
  }

  public double getDegrees() {
    return Math.toDegrees(radians);
  }
}
