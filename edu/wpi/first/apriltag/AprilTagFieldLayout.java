package edu.wpi.first.apriltag;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

public class AprilTagFieldLayout {
  private final Map<Integer, Pose3d> poses = new HashMap<>();

  public AprilTagFieldLayout() {}

  public void setTagPose(int id, Pose3d pose) {
    poses.put(id, pose);
  }

  public Optional<Pose3d> getTagPose(int id) {
    return Optional.ofNullable(poses.get(id));
  }
}
