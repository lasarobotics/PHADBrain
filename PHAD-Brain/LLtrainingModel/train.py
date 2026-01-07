import os
import pathlib
import torch
import torch.nn as nn
import torch.optim as optim
import tensorflow as tf
from torchvision import datasets, transforms

# ----------------------------
# USER DATASET SELECTION
# ----------------------------
BASE_DATA_DIR = pathlib.Path("data")

print("Available datasets:")
print("1) dataSet1")
print("2) dataSet2")

choice = input("Select dataset (1 or 2): ").strip()

if choice == "1":
    DATA_DIR = BASE_DATA_DIR / "dataSet1"
elif choice == "2":
    DATA_DIR = BASE_DATA_DIR / "dataSet2"
else:
    raise ValueError("Invalid selection")

if not DATA_DIR.exists():
    raise FileNotFoundError(DATA_DIR)

print(f"Using dataset: {DATA_DIR}")

# ----------------------------
# SHARED CONFIG
# ----------------------------
IMG_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 20

# ============================================================
# PYTORCH TRAINING (PRIMARY – DEBUG & ITERATION)
# ============================================================

transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
])

dataset = datasets.ImageFolder(DATA_DIR, transform=transform)
loader = torch.utils.data.DataLoader(
    dataset, batch_size=BATCH_SIZE, shuffle=True
)

NUM_CLASSES = len(dataset.classes)
print("Classes:", dataset.classes)


class LLNet(nn.Module):
    def __init__(self, n):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 16, 3, stride=2),
            nn.ReLU(),
            nn.Conv2d(16, 32, 3, stride=2),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, stride=2),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
        )
        self.fc = nn.Linear(64, n)

    def forward(self, x):
        x = self.net(x)
        return self.fc(x.flatten(1))


model = LLNet(NUM_CLASSES)
loss_fn = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)

model.train()
for epoch in range(EPOCHS):
    running_loss = 0.0
    for imgs, labels in loader:
        optimizer.zero_grad()
        out = model(imgs)
        loss = loss_fn(out, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()

    print(f"[Torch] Epoch {epoch+1}/{EPOCHS} | Loss {running_loss:.3f}")

# ----------------------------
# EXPORT ONNX (Limelight OK)
# ----------------------------
dummy = torch.randn(1, 3, IMG_SIZE, IMG_SIZE)
torch.onnx.export(
    model,
    dummy,
    "limelight_model.onnx",
    input_names=["input"],
    output_names=["output"],
    opset_version=11,
)

print("[OK] Exported limelight_model.onnx")

# ============================================================
# TENSORFLOW TRAINING (FINAL DEPLOY FORMAT)
# ============================================================

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    shuffle=True,
)

train_ds = train_ds.map(lambda x, y: (x / 255.0, y))

tf_model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(16, 3, strides=2, activation="relu",
                           input_shape=(IMG_SIZE, IMG_SIZE, 3)),
    tf.keras.layers.Conv2D(32, 3, strides=2, activation="relu"),
    tf.keras.layers.Conv2D(64, 3, strides=2, activation="relu"),
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.Dense(NUM_CLASSES, activation="softmax"),
])

tf_model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

tf_model.fit(train_ds, epochs=EPOCHS)

# ----------------------------
# CONVERT TO TFLITE
# ----------------------------
converter = tf.lite.TFLiteConverter.from_keras_model(tf_model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

with open("limelight_model.tflite", "wb") as f:
    f.write(tflite_model)

print("[OK] Exported limelight_model.tflite")
print("Training complete.")
