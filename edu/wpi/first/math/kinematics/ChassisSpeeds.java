package edu.wpi.first.math.kinematics;

import edu.wpi.first.math.geometry.Rotation2d;

public class ChassisSpeeds {
  public double vxMetersPerSecond;
  public double vyMetersPerSecond;
  public double omegaRadiansPerSecond;

  public ChassisSpeeds() {
    this(0.0, 0.0, 0.0);
  }

  public ChassisSpeeds(double vx, double vy, double omega) {
    this.vxMetersPerSecond = vx;
    this.vyMetersPerSecond = vy;
    this.omegaRadiansPerSecond = omega;
  }

  public static ChassisSpeeds fromFieldRelativeSpeeds(
      double vx, double vy, double omega, Rotation2d robotAngle) {
    double cosA = Math.cos(robotAngle.getRadians());
    double sinA = Math.sin(robotAngle.getRadians());
    double vxRobot = vx * cosA + vy * sinA;
    double vyRobot = -vx * sinA + vy * cosA;
    return new ChassisSpeeds(vxRobot, vyRobot, omega);
  }
}
