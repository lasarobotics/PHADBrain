# LLtrainingModel/pytorch.py

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms

# ----------------------------
# CONFIG
# ----------------------------
DATA_DIR = "data"
IMG_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 15
ONNX_OUT = "limelight_model.onnx"

# ----------------------------
# DATA
# ----------------------------
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
])

dataset = datasets.ImageFolder(DATA_DIR, transform=transform)
loader = torch.utils.data.DataLoader(
    dataset, batch_size=BATCH_SIZE, shuffle=True
)

num_classes = len(dataset.classes)

# ----------------------------
# MODEL
# ----------------------------
class LLNet(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 3),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, 3),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, 3),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        self.classifier = nn.Linear(64, num_classes)

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


model = LLNet(num_classes)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)

# ----------------------------
# TRAIN
# ----------------------------
model.train()
for epoch in range(EPOCHS):
    total_loss = 0
    for imgs, labels in loader:
        optimizer.zero_grad()
        out = model(imgs)
        loss = criterion(out, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    print(f"Epoch {epoch+1}/{EPOCHS} | Loss: {total_loss:.3f}")

# ----------------------------
# EXPORT TO ONNX
# ----------------------------
dummy = torch.randn(1, 3, IMG_SIZE, IMG_SIZE)
torch.onnx.export(
    model,
    dummy,
    ONNX_OUT,
    input_names=["input"],
    output_names=["output"],
    opset_version=11,
)

print(f"[OK] ONNX model saved: {ONNX_OUT}")
print("Classes:", dataset.classes)
