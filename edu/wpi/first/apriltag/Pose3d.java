package edu.wpi.first.apriltag;

import edu.wpi.first.math.geometry.Pose2d;
import edu.wpi.first.math.geometry.Rotation2d;
import edu.wpi.first.math.geometry.Translation2d;

public class Pose3d {
  private final double x;
  private final double y;
  private final double z;

  public Pose3d() {
    this(0.0, 0.0, 0.0);
  }

  public Pose3d(double x, double y, double z) {
    this.x = x;
    this.y = y;
    this.z = z;
  }

  public Pose2d toPose2d() {
    return new Pose2d(new Translation2d(x, y), new Rotation2d());
  }
}
