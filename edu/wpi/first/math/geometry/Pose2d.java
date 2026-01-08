package edu.wpi.first.math.geometry;

public class Pose2d {
  private final Translation2d translation;
  private final Rotation2d rotation;

  public Pose2d() {
    this(new Translation2d(), new Rotation2d());
  }

  public Pose2d(Translation2d translation, Rotation2d rotation) {
    this.translation = translation;
    this.rotation = rotation;
  }

  public Translation2d getTranslation() {
    return translation;
  }

  public Rotation2d getRotation() {
    return rotation;
  }

  public double getX() {
    return translation.getX();
  }

  public double getY() {
    return translation.getY();
  }
}
