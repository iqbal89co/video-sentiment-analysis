# train_local.py
import argparse
import os
import subprocess
import sys
from pathlib import Path

def start_training(
    train_dir: str,
    val_dir: str,
    test_dir: str,
    model_dir: str = "./artifacts",
    epochs: int = 20,
    batch_size: int = 16,
    learning_rate: float = 1e-3,
    python_exe: str = sys.executable,
):
    # Ensure dirs exist
    for p in [train_dir, val_dir, test_dir]:
        if not Path(p).exists():
            raise FileNotFoundError(f"Path not found: {p}")
    os.makedirs(model_dir, exist_ok=True)

    # Optional: match SageMaker env so your train.py defaults still work
    env = os.environ.copy()
    env["SM_CHANNEL_TRAINING"] = str(Path(train_dir).resolve())
    env["SM_CHANNEL_VALIDATION"] = str(Path(val_dir).resolve())
    env["SM_CHANNEL_TEST"] = str(Path(test_dir).resolve())
    env["SM_MODEL_DIR"] = str(Path(model_dir).resolve())

    # Run training/train.py exactly like SageMaker would call the script
    cmd = [
        python_exe,
        "-m",
        "training.train",          # runs training/train.py as a module
        "--epochs", str(epochs),
        "--batch-size", str(batch_size),
        "--learning-rate", str(learning_rate),
        # You can pass explicit dirs too; train.py already reads from SM_* envs,
        # but setting both is harmless and explicit.
        "--train-dir", env["SM_CHANNEL_TRAINING"],
        "--val-dir", env["SM_CHANNEL_VALIDATION"],
        "--test-dir", env["SM_CHANNEL_TEST"],
        "--model-dir", env["SM_MODEL_DIR"],
    ]
    print("Launching:", " ".join(cmd))
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

def _parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", default="./artifacts", help="Where to save model.pth")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--learning-rate", type=float, default=1e-3)
    ap.add_argument("--python", default=sys.executable, help="Python executable to use")
    return ap.parse_args()

if __name__ == "__main__":
    args = _parse_args()
    start_training(
        train_dir='dataset/train',
        val_dir='dataset/dev',
        test_dir='dataset/test',
        model_dir=args.model_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        python_exe=args.python,
    )
