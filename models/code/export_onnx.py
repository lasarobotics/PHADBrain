from pathlib import Path
import shutil
import os
import torch
from functools import wraps
from ultralytics import YOLO
from ultralytics.nn.tasks import DetectionModel


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def clean_dir(path: Path):
    if path.exists():
        shutil.rmtree(path)


def latest_model_dir(base: Path) -> Path:
    dirs = [d for d in base.iterdir() if d.is_dir()]
    if not dirs:
        raise FileNotFoundError(f"No model directories in {base}")
    return max(dirs, key=lambda p: p.stat().st_mtime)


def find_weight(root: Path, name: str) -> Path:
    for p in root.rglob(name):
        if p.is_file():
            return p
    return root / name


def find_onnx(root: Path) -> Path:
    for p in root.rglob("*.onnx"):
        if p.is_file():
            return p
    return root / "best.onnx"


def main():
    root = Path(__file__).resolve().parents[2]
    os.chdir(root)
    os.environ["TORCH_LOAD_WEIGHTS_ONLY"] = "0"
    torch.serialization.add_safe_globals([DetectionModel])
    orig_load = torch.load

    @wraps(orig_load)
    def _load(*args, **kwargs):
        kwargs.setdefault("weights_only", False)
        return orig_load(*args, **kwargs)

    torch.load = _load
    base_models_dir = Path("models/models")
    model_dir = latest_model_dir(base_models_dir)
    weights_dir = model_dir / "weights"
    exports_dir = model_dir / "exports"
    ensure_dir(exports_dir)

    best_weights = find_weight(weights_dir, "best.pt")
    if not best_weights.exists():
        last_weights = find_weight(weights_dir, "last.pt")
        if last_weights.exists():
            shutil.copy2(last_weights, best_weights)
        else:
            raise FileNotFoundError(f"Missing weights: {best_weights}")

    export_run = model_dir / "export_run"
    clean_dir(export_run)
    ensure_dir(export_run)

    model = YOLO(str(best_weights))
    model.export(
        format="onnx",
        imgsz=640,
        project=str(export_run),
        name="export",
        opset=12,
        device="cpu",
        dynamic=False,
        simplify=False,
        half=False,
    )

    onnx_src = find_onnx(export_run)
    if not onnx_src.exists():
        onnx_src = find_onnx(model_dir)
    onnx_dst = exports_dir / "best.onnx"
    if onnx_src.exists():
        shutil.copy2(onnx_src, onnx_dst)
    else:
        raise FileNotFoundError("ONNX export failed: best.onnx not found")


if __name__ == "__main__":
    main()
