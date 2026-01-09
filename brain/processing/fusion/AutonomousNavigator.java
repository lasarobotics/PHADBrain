package brain.processing.fusion;

import edu.wpi.first.apriltag.AprilTagFieldLayout;
import edu.wpi.first.math.controller.PIDController;
import edu.wpi.first.math.geometry.Pose2d;
import edu.wpi.first.math.geometry.Rotation2d;
import edu.wpi.first.math.geometry.Translation2d;
import edu.wpi.first.math.kinematics.ChassisSpeeds;
import java.util.HashMap;
import java.util.List;
import java.util.Optional;
import java.util.PriorityQueue;

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
  private final boolean useAStar = true;
  private final double gridResolution = 0.3;
  private final int maxAStarIters = 400;

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
    Translation2d repulsion = computeRepulsion(current, toTarget, obstacles);
    Translation2d desired = useAStar
        ? aStarDirection(current, target, obstacles, repulsion)
        : attraction.plus(repulsion);
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

  private Translation2d computeRepulsion(Translation2d current, Translation2d toTarget, List<Obstacle> obstacles) {
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
    return repulsion;
  }

  private Translation2d aStarDirection(
      Translation2d start, Translation2d goal, List<Obstacle> obstacles, Translation2d repulsion) {
    Cell s = new Cell(0, 0);
    Translation2d offset = start;
    Translation2d delta = goal.minus(start);
    int gx = (int) Math.round(delta.getX() / gridResolution);
    int gy = (int) Math.round(delta.getY() / gridResolution);
    Cell g = new Cell(gx, gy);
    HashMap<Cell, Cell> came = new HashMap<>();
    HashMap<Cell, Double> gScore = new HashMap<>();
    PriorityQueue<Node> open = new PriorityQueue<>((a, b) -> Double.compare(a.f, b.f));
    gScore.put(s, 0.0);
    open.add(new Node(s, h(s, g)));
    int iters = 0;
    while (!open.isEmpty() && iters < maxAStarIters) {
      Node n = open.poll();
      iters++;
      if (n.cell.equals(g)) {
        break;
      }
      for (Cell nb : neighbors(n.cell)) {
        if (isBlocked(nb, obstacles, offset)) {
          continue;
        }
        double tentative = gScore.getOrDefault(n.cell, 1e9) + gridResolution;
        if (tentative < gScore.getOrDefault(nb, 1e9)) {
          came.put(nb, n.cell);
          gScore.put(nb, tentative);
          double f = tentative + h(nb, g);
          open.add(new Node(nb, f));
        }
      }
    }
    if (!came.containsKey(g)) {
      return start.equals(goal) ? new Translation2d() : delta.div(delta.getNorm()).plus(repulsion);
    }
    Cell step = g;
    while (came.containsKey(step) && !came.get(step).equals(s)) {
      step = came.get(step);
    }
    Translation2d dir = new Translation2d(step.x * gridResolution, step.y * gridResolution);
    Translation2d res = dir;
    if (res.getNorm() > 1e-4) {
      res = res.div(res.getNorm());
    }
    res = res.plus(repulsion);
    if (res.getNorm() > 1e-4) {
      res = res.div(res.getNorm());
    }
    return res;
  }

  private Iterable<Cell> neighbors(Cell c) {
    java.util.List<Cell> list = new java.util.ArrayList<>(4);
    list.add(new Cell(c.x + 1, c.y));
    list.add(new Cell(c.x - 1, c.y));
    list.add(new Cell(c.x, c.y + 1));
    list.add(new Cell(c.x, c.y - 1));
    return list;
  }

  private double h(Cell a, Cell b) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    return Math.hypot(dx, dy) * gridResolution;
  }

  private boolean isBlocked(Cell c, List<Obstacle> obstacles, Translation2d offset) {
    Translation2d p = new Translation2d(c.x * gridResolution, c.y * gridResolution).plus(offset);
    for (Obstacle o : obstacles) {
      if (p.getDistance(o.center) < o.radiusMeters + obstacleInfluenceMeters * 0.5) {
        return true;
      }
    }
    return false;
  }

  private static final class Cell {
    final int x;
    final int y;
    Cell(int x, int y) {
      this.x = x;
      this.y = y;
    }
    @Override
    public boolean equals(Object o) {
      if (this == o) return true;
      if (!(o instanceof Cell)) return false;
      Cell c = (Cell) o;
      return x == c.x && y == c.y;
    }
    @Override
    public int hashCode() {
      return 31 * x + y;
    }
  }

  private static final class Node {
    final Cell cell;
    final double f;
    Node(Cell cell, double f) {
      this.cell = cell;
      this.f = f;
    }
  }
}
