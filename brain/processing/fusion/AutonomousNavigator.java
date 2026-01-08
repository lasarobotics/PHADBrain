package brain.processing.fusion;

import edu.wpi.first.apriltag.AprilTagFieldLayout;
import edu.wpi.first.math.controller.PIDController;
import edu.wpi.first.math.geometry.Pose2d;
import edu.wpi.first.math.geometry.Rotation2d;
import edu.wpi.first.math.geometry.Translation2d;
import edu.wpi.first.math.kinematics.ChassisSpeeds;
import java.util.List;
import java.util.Optional;

public class AutonomousNavigator {
  public static final class Obstacle {
    public final Translation2d center;
    public final double radiusMeters;

    public Obstacle(Translation2d center, double radiusMeters) {
      this.center = center;
      this.radiusMeters = radiusMeters;
    }
  }

  private final double maxSpeedMetersPerSec;
  private final double maxOmegaRadPerSec;
  private final double obstacleInfluenceMeters;
  private final double obstacleRepulsionGain;
  private final AprilTagFieldLayout fieldLayout;

  private final double massKg;
  private final double comHeightMeters;
  private final double trackWidthMeters;
  private final double wheelbaseMeters;
  private final double frictionCoefficient;

  private final PIDController headingPid;

  public AutonomousNavigator(
      double maxSpeedMetersPerSec,
      double maxOmegaRadPerSec,
      double kPHeading,
      double obstacleInfluenceMeters,
      double obstacleRepulsionGain,
      AprilTagFieldLayout fieldLayout,
      double massKg,
      double comHeightMeters,
      double trackWidthMeters,
      double wheelbaseMeters,
      double frictionCoefficient) {
    this.maxSpeedMetersPerSec = maxSpeedMetersPerSec;
    this.maxOmegaRadPerSec = maxOmegaRadPerSec;
    this.obstacleInfluenceMeters = obstacleInfluenceMeters;
    this.obstacleRepulsionGain = obstacleRepulsionGain;
    this.fieldLayout = fieldLayout;
    this.massKg = massKg;
    this.comHeightMeters = comHeightMeters;
    this.trackWidthMeters = trackWidthMeters;
    this.wheelbaseMeters = wheelbaseMeters;
    this.frictionCoefficient = frictionCoefficient;

    this.headingPid = new PIDController(kPHeading, 0, 0);
    this.headingPid.enableContinuousInput(-Math.PI, Math.PI);
  }

  public ChassisSpeeds update(Pose2d currentPose, int targetTagId, List<Obstacle> obstacles) {
    Optional<Pose2d> targetPoseOpt = fieldLayout.getTagPose(targetTagId).map(p -> p.toPose2d());
    if (!targetPoseOpt.isPresent()) {
      return new ChassisSpeeds();
    }
    Pose2d targetPose = targetPoseOpt.get();

    Translation2d current = currentPose.getTranslation();
    Translation2d target = targetPose.getTranslation();
    Translation2d toTarget = target.minus(current);
    double distanceToTarget = toTarget.getNorm();
    if (distanceToTarget < 1e-3) {
      return new ChassisSpeeds();
    }

    Translation2d attraction = toTarget.div(distanceToTarget);

    Translation2d repulsion = new Translation2d();
    for (Obstacle obs : obstacles) {
      Translation2d line = toTarget;
      Translation2d obsVec = obs.center.minus(current);
      double lineNormSq = line.getNorm() * line.getNorm();
      if (lineNormSq < 1e-9) {
        continue;
      }
      double proj = obsVec.dot(line) / lineNormSq;
      proj = Math.max(0.0, Math.min(1.0, proj));
      Translation2d closest = current.plus(line.times(proj));
      double distToLine = obs.center.getDistance(closest);
      double influenceRadius = obs.radiusMeters + obstacleInfluenceMeters;
      if (distToLine < influenceRadius) {
        double strength = obstacleRepulsionGain * (influenceRadius - distToLine) / influenceRadius;
        Translation2d away = closest.minus(obs.center);
        if (away.getNorm() > 1e-4) {
          repulsion = repulsion.plus(away.div(away.getNorm()).times(strength));
        }
      }
    }

    Translation2d desired = attraction.plus(repulsion);
    if (desired.getNorm() < 1e-4) {
      desired = new Translation2d();
    }

    double maxAccel = computeMaxAccelMetersPerSec2();
    double speedLimitFromDistance = Math.sqrt(Math.max(0.0, 2 * maxAccel * distanceToTarget));
    double commandedSpeed = Math.min(maxSpeedMetersPerSec, speedLimitFromDistance);

    if (desired.getNorm() > 1e-4) {
      desired = desired.div(desired.getNorm()).times(commandedSpeed);
    }

    Rotation2d desiredHeading = new Rotation2d(Math.atan2(toTarget.getY(), toTarget.getX()));
    double omega =
        headingPid.calculate(currentPose.getRotation().getRadians(), desiredHeading.getRadians());
    omega = Math.max(-maxOmegaRadPerSec, Math.min(maxOmegaRadPerSec, omega));

    return ChassisSpeeds.fromFieldRelativeSpeeds(
        desired.getX(), desired.getY(), omega, currentPose.getRotation());
  }

  private double computeMaxAccelMetersPerSec2() {
    double gravity = 9.81;
    double frictionLimited = frictionCoefficient * gravity;
    double halfTrack = trackWidthMeters / 2.0;
    double halfWheelbase = wheelbaseMeters / 2.0;
    double tipLimit =
        gravity * Math.min(halfTrack, halfWheelbase) / Math.max(comHeightMeters, 1e-3);
    double inertiaPenalty = Math.max(1.0, massKg / 50.0);
    double linearAccel = Math.min(frictionLimited, tipLimit) / inertiaPenalty;
    return Math.max(0.5, linearAccel);
  }
}
