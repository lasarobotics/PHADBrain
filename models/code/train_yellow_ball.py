from pathlib import Path
from datetime import datetime
import shutil
import os
from ultralytics import YOLO
import torch
from ultralytics.nn.tasks import DetectionModel
from functools import wraps
from PIL import ImageFont
import torch.backends.mps


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def clean_dir(path: Path):
    if path.exists():
        shutil.rmtree(path)


def next_stamp(base_dir: Path) -> str:
    base = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    version = 1
    while True:
        stamp = f"{base}_v{version}"
        if not (base_dir / stamp).exists():
            return stamp
        version += 1


def write_labels(model_dir: Path):
    labels_file = model_dir / "labels.txt"
    labels_file.write_text("yellow_ball\n", encoding="utf-8")


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
    if not hasattr(ImageFont.FreeTypeFont, "getsize"):
        def _getsize(self, text):
            box = self.getbbox(text)
            return box[2] - box[0], box[3] - box[1]
        ImageFont.FreeTypeFont.getsize = _getsize
    data_yaml = Path("models/data/Yellow Ball Finder.v1i.yolov8/data.yaml")
    base_models_dir = Path("models/models")
    stamp = next_stamp(base_models_dir)
    model_dir = base_models_dir / stamp
    weights_dir = model_dir / "weights"
    exports_dir = model_dir / "exports"
    clean_dir(model_dir)
    ensure_dir(weights_dir)
    ensure_dir(exports_dir)
    write_labels(model_dir)

    train_run = model_dir / "train_run"
    clean_dir(train_run)
    ensure_dir(train_run)
    ensure_dir(train_run / "weights")

    old_cwd = Path.cwd()
    os.chdir(data_yaml.parent)

    model = YOLO("yolov8n.pt")

    try:
        epochs_input = input("Enter epoch count (default 40): ").strip()
        epochs_val = int(epochs_input) if epochs_input else 40
    except Exception:
        epochs_val = 40

    if torch.cuda.is_available():
        device = "0"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    results = model.train(
        data=str(data_yaml.name),
        imgsz=640,
        epochs=epochs_val,
        optimizer="AdamW",
        device=device,
        project=str(model_dir),
        name="train_run",
        exist_ok=True,
        save=True,
        plots=False,
        save_json=False,
        save_txt=False,
        save_conf=False,
        save_crop=False,
        show=False,
        verbose=False,
        half=False,
    )
    os.chdir(old_cwd)

    save_dir = Path(model_dir) / "train_run"
    if results is not None and hasattr(results, "save_dir"):
        save_dir = Path(results.save_dir)
    elif hasattr(model, "trainer") and hasattr(model.trainer, "save_dir"):
        save_dir = Path(model.trainer.save_dir)

    def find_weight(root: Path, name: str) -> Path:
        for p in root.rglob(name):
            if p.is_file():
                return p
        return root / "weights" / name

    best_src = find_weight(save_dir, "best.pt")
    last_src = find_weight(save_dir, "last.pt")
    clean_dir(weights_dir)
    ensure_dir(weights_dir)
    best_dst = weights_dir / "best.pt"
    last_dst = weights_dir / "last.pt"
    if best_src.exists():
        shutil.copy2(best_src, best_dst)
    if last_src.exists():
        shutil.copy2(last_src, last_dst)
    if not best_dst.exists() and last_dst.exists():
        shutil.copy2(last_dst, best_dst)
    if not best_dst.exists():
        base_weight = root / "yolov8n.pt"
        if base_weight.exists():
            shutil.copy2(base_weight, best_dst)
            shutil.copy2(base_weight, last_dst)
        else:
            raise FileNotFoundError("Missing best.pt and last.pt from training output")


if __name__ == "__main__":
    main()
