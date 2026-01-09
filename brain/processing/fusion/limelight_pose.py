import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Tuple


@dataclass
class Rotation2d:
    radians: float

    @classmethod
    def from_degrees(cls, degrees: float) -> "Rotation2d":
        return cls(math.radians(degrees))

    def get_degrees(self) -> float:
        return math.degrees(self.radians)


@dataclass
class Translation2d:
    x: float
    y: float


@dataclass
class Pose2d:
    translation: Translation2d
    rotation: Rotation2d

    def get_x(self) -> float:
        return self.translation.x

    def get_y(self) -> float:
        return self.translation.y

    def get_rotation(self) -> Rotation2d:
        return self.rotation


@dataclass
class CameraConfig:
    name: str
    target_distance_feet: float = 2.0
    angle_tolerance_deg: float = 2.0
    distance_tolerance_feet: float = 0.3
    mount_angle_x_deg: float = 40.0
    mount_angle_y_deg: float = 99.846552
    height_inches: float = 9.5
    offset_x_inches: float = 8.41
    offset_y_inches: float = 11.6
    mirror_tx: bool = False


class NetworkTablesInterface(Protocol):
    def get_double(self, key: str, default: float = 0.0) -> float:
        ...

    def get_double_array(self, key: str, default: List[float]) -> List[float]:
        ...


class MultiLimelightPose:
    def __init__(
        self,
        nt_client: NetworkTablesInterface,
        tag_layout: Optional[Dict[int, Tuple[float, float, float]]] = None,
        camera_configs: Optional[List[CameraConfig]] = None,
    ) -> None:
        self.nt_client = nt_client
        self.tag_layout = tag_layout or {}
        cfg = self._load_constants()
        self.cameras = camera_configs or self._build_cameras_from_constants(cfg)
        self.last_pose: Dict[str, Optional[Pose2d]] = {cam.name: None for cam in self.cameras}
        self.last_seen: Dict[str, float] = {cam.name: 0.0 for cam in self.cameras}
        self.last_tx: Dict[str, Optional[float]] = {cam.name: None for cam in self.cameras}
        self.last_corners: Dict[str, Optional[List[float]]] = {cam.name: None for cam in self.cameras}
        self.last_tag: Dict[str, int] = {cam.name: -1 for cam in self.cameras}
        self.dropout_speed_scale = float(cfg.get("limelight", {}).get("dropout_speed_scale", 0.6))
        self.occlusion_window = float(cfg.get("limelight", {}).get("occlusion_window", 0.15))

    def _entry_key(self, cam: CameraConfig, key: str) -> str:
        return f"{cam.name}/{key}"

    def _load_constants(self) -> Dict:
        root = Path(__file__).resolve().parent.parent.parent
        cfg_path = root / "constants.json"
        if cfg_path.exists():
            try:
                with cfg_path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _build_cameras_from_constants(self, cfg: Dict) -> List[CameraConfig]:
        cams_cfg = cfg.get("cameras")
        if not isinstance(cams_cfg, list) or len(cams_cfg) == 0:
            return [
                CameraConfig(name="limelight-left", mirror_tx=False, offset_x_inches=8.41),
                CameraConfig(name="limelight-right", mirror_tx=True, offset_x_inches=-8.41),
            ]
        cams: List[CameraConfig] = []
        for c in cams_cfg:
            cams.append(
                CameraConfig(
                    name=str(c.get("name", "limelight")),
                    target_distance_feet=float(c.get("target_distance_feet", 2.0)),
                    angle_tolerance_deg=float(c.get("angle_tolerance_deg", 2.0)),
                    distance_tolerance_feet=float(c.get("distance_tolerance_feet", 0.3)),
                    mount_angle_x_deg=float(c.get("mount_angle_x_deg", 40.0)),
                    mount_angle_y_deg=float(c.get("mount_angle_y_deg", 99.846552)),
                    height_inches=float(c.get("height_inches", 9.5)),
                    offset_x_inches=float(c.get("offset_x_inches", 8.41)),
                    offset_y_inches=float(c.get("offset_y_inches", 11.6)),
                    mirror_tx=bool(c.get("mirror_tx", False)),
                )
            )
        return cams

    def _parse_botpose(self, cam: CameraConfig, suffix: str) -> Optional[Pose2d]:
        data = self.nt_client.get_double_array(self._entry_key(cam, suffix), [])
        if len(data) < 6:
            return None
        x_m, y_m, yaw_deg = data[0], data[1], data[5]
        return Pose2d(Translation2d(x_m, y_m), Rotation2d.from_degrees(yaw_deg))

    def _limelight_pose(self, cam: CameraConfig) -> Optional[Pose2d]:
        for suffix in ("botpose", "botpose_wpiblue", "botpose_wpired"):
            pose = self._parse_botpose(cam, suffix)
            if pose:
                return pose
        return None

    def _parse_targetpose_robotspace(self, cam: CameraConfig) -> Optional[float]:
        data = self.nt_client.get_double_array(self._entry_key(cam, "targetpose_robotspace"), [])
        if len(data) < 3:
            return None
        tx_val, ty_val, tz_val = data[0], data[1], data[2]
        return math.sqrt(tx_val * tx_val + ty_val * ty_val + tz_val * tz_val)

    def _tag_height_inches(self, tag_id: int) -> Optional[float]:
        if tag_id not in self.tag_layout:
            return None
        tag = self.tag_layout[tag_id]
        if len(tag) >= 4:
            return float(tag[3]) * 39.3701
        return None

    def _calculate_tag_area(self, corners: List[float]) -> float:
        x0, y0, x1, y1, x2, y2, x3, y3 = corners[:8]
        h_left = abs(y3 - y0)
        h_right = abs(y2 - y1)
        w_top = abs(x2 - x3)
        w_bottom = abs(x1 - x0)
        avg_height = (h_left + h_right) / 2.0
        avg_width = (w_top + w_bottom) / 2.0
        return avg_width * avg_height

    def _distance_from_area(self, area: float) -> float:
        return 12.23504 * math.pow(0.999818, area) + 1.19735

    def _manual_pose(self, cam: CameraConfig, tx: float, corners: List[float], tag_id: int) -> Optional[Pose2d]:
        if tag_id == -1 or len(corners) < 8:
            return None
        if tag_id not in self.tag_layout:
            return None
        tag_x, tag_y, tag_rot_deg = self.tag_layout[tag_id]
        tag_pose = Pose2d(Translation2d(tag_x, tag_y), Rotation2d.from_degrees(tag_rot_deg))
        real_time_ta = self._calculate_tag_area(corners)
        camera_distance = self._distance_from_area(real_time_ta)
        camera_offset_distance = math.hypot(
            cam.offset_x_inches / 12.0, cam.offset_y_inches / 12.0
        )
        horizontal_angle_error = -tx if cam.mirror_tx else tx
        adjusted_camera_distance = camera_distance / math.cos(math.radians(cam.mount_angle_y_deg))
        robot_center_distance = math.sqrt(
            math.pow(adjusted_camera_distance, 2)
            + math.pow(camera_offset_distance, 2)
            - 2
            * adjusted_camera_distance
            * camera_offset_distance
            * math.cos(math.radians(horizontal_angle_error + cam.mount_angle_x_deg))
        )
        current_distance = robot_center_distance + 1.0
        distance_meters = current_distance * 0.3048
        robot_angle_to_tag = tag_pose.get_rotation().get_degrees() + 180 - horizontal_angle_error
        robot_rotation = Rotation2d.from_degrees(robot_angle_to_tag)
        angle_rad = math.radians(robot_angle_to_tag)
        robot_x = tag_pose.get_x() - distance_meters * math.cos(angle_rad)
        robot_y = tag_pose.get_y() - distance_meters * math.sin(angle_rad)
        return Pose2d(Translation2d(robot_x, robot_y), robot_rotation)

    def _movement(self, cam: CameraConfig, tx: float, corners: List[float]) -> Dict[str, float]:
        real_time_ta = self._calculate_tag_area(corners)
        camera_distance = self._distance_from_area(real_time_ta)
        camera_offset_distance = math.hypot(
            cam.offset_x_inches / 12.0, cam.offset_y_inches / 12.0
        )
        horizontal_angle_error = -tx if cam.mirror_tx else tx
        adjusted_camera_distance = camera_distance / math.cos(math.radians(cam.mount_angle_y_deg))
        robot_center_distance = math.sqrt(
            math.pow(adjusted_camera_distance, 2)
            + math.pow(camera_offset_distance, 2)
            - 2
            * adjusted_camera_distance
            * camera_offset_distance
            * math.cos(math.radians(horizontal_angle_error + cam.mount_angle_x_deg))
        )
        current_distance = robot_center_distance + 1.0
        forward_movement = current_distance - cam.target_distance_feet
        strafe_movement = current_distance * math.tan(math.radians(horizontal_angle_error))
        rotation_required = horizontal_angle_error
        return {
            "camera_distance_feet": camera_distance,
            "robot_center_distance_feet": robot_center_distance,
            "current_distance_feet": current_distance,
            "target_distance_feet": cam.target_distance_feet,
            "horizontal_angle_error_deg": horizontal_angle_error,
            "forward_feet": forward_movement,
            "strafe_feet": strafe_movement,
            "rotation_deg": rotation_required,
        }

    def _command(self, cam: CameraConfig, forward: float, strafe: float, rotation: float) -> str:
        if abs(forward) < cam.distance_tolerance_feet and abs(rotation) < cam.angle_tolerance_deg:
            return "ALIGNED - Hold position"
        parts: List[str] = []
        if abs(rotation) > cam.angle_tolerance_deg:
            parts.append(f"ROTATE {abs(rotation):.1f} deg {'RIGHT' if rotation > 0 else 'LEFT'}")
        if abs(forward) > cam.distance_tolerance_feet:
            parts.append(f"DRIVE {abs(forward):.2f} ft {'BACKWARD' if forward > 0 else 'FORWARD'}")
        else:
            parts.append("HOLD DISTANCE")
        if abs(strafe) > 0.1:
            parts.append(f"STRAFE {abs(strafe):.2f} ft {'RIGHT' if strafe > 0 else 'LEFT'}")
        return " -> ".join(parts)

    def _alignment(self, cam: CameraConfig, forward_error: float, rotation_error: float) -> bool:
        return abs(forward_error) < cam.distance_tolerance_feet and abs(rotation_error) < cam.angle_tolerance_deg

    def _update_detections(self, cam: CameraConfig) -> List[Dict[str, float]]:
        data = self.nt_client.get_double_array(self._entry_key(cam, "rawdetections"), [])
        detections: List[Dict[str, float]] = []
        stride = 13
        for i in range(0, len(data), stride):
            if i + stride > len(data):
                break
            det = {
                "id": data[i + 0],
                "tx": data[i + 1],
                "ty": data[i + 2],
                "ta": data[i + 3],
                "corners": [
                    data[i + 4],
                    data[i + 5],
                    data[i + 6],
                    data[i + 7],
                    data[i + 8],
                    data[i + 9],
                    data[i + 10],
                    data[i + 11],
                ],
            }
            detections.append(det)
        return detections

    def _camera_step(self, cam: CameraConfig, now: float) -> Dict[str, float]:
        tv = self.nt_client.get_double(self._entry_key(cam, "tv"), 0.0)
        tx = self.nt_client.get_double(self._entry_key(cam, "tx"), 0.0)
        ty = self.nt_client.get_double(self._entry_key(cam, "ty"), 0.0)
        ta = self.nt_client.get_double(self._entry_key(cam, "ta"), 0.0)
        corners = self.nt_client.get_double_array(self._entry_key(cam, "tcornxy"), [0.0] * 8)
        tag_id = int(self.nt_client.get_double(self._entry_key(cam, "tid"), -1.0))
        detections = self._update_detections(cam)

        has_measurement = tv == 1 and len(corners) >= 8
        status = "ok" if has_measurement else "lost"
        velocity_scale = 1.0

        if has_measurement:
            self.last_seen[cam.name] = now
            self.last_corners[cam.name] = list(corners)
            self.last_tx[cam.name] = tx
            self.last_tag[cam.name] = tag_id
        elif self.last_pose[cam.name] is not None and self.last_corners[cam.name] is not None and self.last_tx[cam.name] is not None and self.last_tag[cam.name] != -1:
            corners = self.last_corners[cam.name]
            tx = self.last_tx[cam.name]
            tag_id = self.last_tag[cam.name]
            status = "degraded"
            velocity_scale = self.dropout_speed_scale
        else:
            return {"status": "lost", "camera": cam.name, "velocity_scale": 0.0, "tag_id": tag_id}

        movement = self._movement(cam, tx, corners)
        if status == "degraded":
            movement["forward_feet"] *= self.dropout_speed_scale
            movement["strafe_feet"] *= self.dropout_speed_scale
            movement["rotation_deg"] *= self.dropout_speed_scale
        command = self._command(cam, movement["forward_feet"], movement["strafe_feet"], movement["rotation_deg"])
        aligned = self._alignment(cam, movement["forward_feet"], movement["rotation_deg"])

        target_distance_m = self._parse_targetpose_robotspace(cam)
        tag_height_in = self._tag_height_inches(tag_id)
        megatag2_distance_feet: Optional[float] = None
        if tag_height_in is not None:
            denom = math.tan(math.radians(cam.mount_angle_y_deg + ty))
            if abs(denom) > 1e-6:
                megatag2_distance_feet = ((tag_height_in - cam.height_inches) / 12.0) / denom

        limelight_pose = self._limelight_pose(cam)
        manual_pose = self._manual_pose(cam, tx, corners, tag_id)
        pose = limelight_pose or manual_pose
        if has_measurement and pose:
            self.last_pose[cam.name] = pose

        result: Dict[str, float] = {
            "camera": cam.name,
            "tx": tx,
            "ty": ty,
            "ta": ta,
            "tag_id": tag_id,
            "command": command,
            "aligned": aligned,
            "status": status,
            "velocity_scale": velocity_scale,
            **movement,
        }
        if target_distance_m is not None:
            result["target_distance_m"] = target_distance_m
        if megatag2_distance_feet is not None:
            result["megatag2_distance_feet"] = megatag2_distance_feet
        if pose:
            result.update(
                {
                    "pose_x_m": pose.get_x(),
                    "pose_y_m": pose.get_y(),
                    "pose_rot_deg": pose.get_rotation().get_degrees(),
                }
            )
        if limelight_pose and manual_pose:
            dx = manual_pose.get_x() - limelight_pose.get_x()
            dy = manual_pose.get_y() - limelight_pose.get_y()
            drot = manual_pose.get_rotation().get_degrees() - limelight_pose.get_rotation().get_degrees()
            result.update(
                {
                    "pose_lime_x_m": limelight_pose.get_x(),
                    "pose_lime_y_m": limelight_pose.get_y(),
                    "pose_lime_rot_deg": limelight_pose.get_rotation().get_degrees(),
                    "pose_manual_x_m": manual_pose.get_x(),
                    "pose_manual_y_m": manual_pose.get_y(),
                    "pose_manual_rot_deg": manual_pose.get_rotation().get_degrees(),
                    "pose_dx_m": dx,
                    "pose_dy_m": dy,
                    "pose_drot_deg": drot,
                }
            )
        if detections:
            first = detections[0]
            if len(first["corners"]) >= 8:
                det_move = self._movement(cam, first["tx"], first["corners"])
                det_cmd = self._command(cam, det_move["forward_feet"], det_move["strafe_feet"], det_move["rotation_deg"])
                det_aligned = self._alignment(cam, det_move["forward_feet"], det_move["rotation_deg"])
                result.update(
                    {
                        "det_id": first["id"],
                        "det_tx": first["tx"],
                        "det_ty": first["ty"],
                        "det_ta": first["ta"],
                        "det_cmd": det_cmd,
                        "det_aligned": det_aligned,
                        "det_forward_feet": det_move["forward_feet"],
                        "det_strafe_feet": det_move["strafe_feet"],
                        "det_rotation_deg": det_move["rotation_deg"],
                        "det_current_distance_feet": det_move["current_distance_feet"],
                    }
                )
        return result

    def step(self) -> Dict[str, object]:
        now = time.time()
        per_cam: List[Dict[str, float]] = []
        poses_x: List[float] = []
        poses_y: List[float] = []
        poses_rot: List[float] = []
        distances_m: List[float] = []
        megatag2_distances_m: List[float] = []
        velocity_scale = 1.0
        for cam in self.cameras:
            res = self._camera_step(cam, now)
            per_cam.append(res)
            if "pose_x_m" in res and "pose_y_m" in res and "pose_rot_deg" in res:
                poses_x.append(res["pose_x_m"])
                poses_y.append(res["pose_y_m"])
                poses_rot.append(res["pose_rot_deg"])
            if "target_distance_m" in res:
                distances_m.append(res["target_distance_m"])
            else:
                if "current_distance_feet" in res:
                    distances_m.append(res["current_distance_feet"] * 0.3048)
            if "megatag2_distance_feet" in res:
                megatag2_distances_m.append(res["megatag2_distance_feet"] * 0.3048)
            if "velocity_scale" in res:
                velocity_scale = min(velocity_scale, res["velocity_scale"])

        final_pose: Optional[Tuple[float, float, float]] = None
        if poses_x and poses_y and poses_rot:
            final_pose = (
                sum(poses_x) / len(poses_x),
                sum(poses_y) / len(poses_y),
                sum(poses_rot) / len(poses_rot),
            )

        final_distance_m: Optional[float] = None
        if distances_m:
            final_distance_m = sum(distances_m) / len(distances_m)
        final_megatag2_distance_m: Optional[float] = None
        if megatag2_distances_m:
            final_megatag2_distance_m = sum(megatag2_distances_m) / len(megatag2_distances_m)

        occlusion = False
        if all(res.get("status") == "lost" for res in per_cam):
            if all((now - self.last_seen.get(res.get("camera", ""), 0.0)) < self.occlusion_window for res in per_cam):
                occlusion = True
                velocity_scale = 0.0

        return {
            "cameras": per_cam,
            "final_pose": final_pose,
            "final_distance_m": final_distance_m,
            "final_megatag2_distance_m": final_megatag2_distance_m,
            "final_velocity_scale": velocity_scale,
            "occlusion": occlusion,
        }
