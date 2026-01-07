# LLtrainingModel/tflite.py

import tensorflow as tf
from tensorflow.keras import layers, models
import pathlib

# ----------------------------
# CONFIG
# ----------------------------
DATA_DIR = pathlib.Path("data")  # data/class_name/*.jpg
IMG_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 15
MODEL_OUT = "limelight_model.tflite"

# ----------------------------
# LOAD DATA
# ----------------------------
train_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    shuffle=True,
)

class_names = train_ds.class_names
num_classes = len(class_names)

# Normalize
train_ds = train_ds.map(lambda x, y: (x / 255.0, y))

# ----------------------------
# MODEL (lightweight CNN)
# ----------------------------
model = models.Sequential([
    layers.Conv2D(16, 3, activation="relu", input_shape=(IMG_SIZE, IMG_SIZE, 3)),
    layers.MaxPooling2D(),

    layers.Conv2D(32, 3, activation="relu"),
    layers.MaxPooling2D(),

    layers.Conv2D(64, 3, activation="relu"),
    layers.GlobalAveragePooling2D(),

    layers.Dense(64, activation="relu"),
    layers.Dense(num_classes, activation="softmax"),
])

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

# ----------------------------
# TRAIN
# ----------------------------
model.fit(train_ds, epochs=EPOCHS)

# ----------------------------
# CONVERT TO TFLITE
# ----------------------------
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

with open(MODEL_OUT, "wb") as f:
    f.write(tflite_model)

print(f"[OK] TFLite model saved: {MODEL_OUT}")
print("Classes:", class_names)
