import sys

import modal
import train

app = modal.App("video-sentiment-model")
image = (modal.Image.debian_slim()
            .pip_install_from_requirements("requirements.txt")
            .apt_install(["wget", "unzip", "ffmpeg", "libsndfile1"])
            .run_commands([
                "cd /tmp && wget https://huggingface.co/datasets/declare-lab/MELD/resolve/main/MELD.Raw.tar.gz",
                "cd /tmp && tar -xzf MELD.Raw.tar.gz",
                "mkdir -p /opt/meld-data",
                "mkdir /opt/meld-data/dev",
                "mkdir /opt/meld-data/test",
                "mkdir /opt/meld-data/train",
                "cp -r /tmp/MELD.Raw/* /opt/meld-data/",
                "rm -rf /tmp/MELD.Raw",
                "rm /tmp/MELD.Raw.tar.gz",
                "mv /opt/meld-data/dev_sent_emo.csv /opt/meld-data/dev/",
                "mv /opt/meld-data/test_sent_emo.csv /opt/meld-data/test/",
                "mv /opt/meld-data/dev.tar.gz /opt/meld-data/dev/",
                "mv /opt/meld-data/test.tar.gz /opt/meld-data/test/",
                "mv /opt/meld-data/train.tar.gz /opt/meld-data/train/",
                "tar -xzf /opt/meld-data/dev/dev.tar.gz -C /opt/meld-data/dev/",
                "tar -xzf /opt/meld-data/test/test.tar.gz -C /opt/meld-data/test/",
                "tar -xzf /opt/meld-data/train/train.tar.gz -C /opt/meld-data/train/",
                "rm /opt/meld-data/dev/dev.tar.gz",
                "rm /opt/meld-data/test/test.tar.gz",
                "rm /opt/meld-data/train/train.tar.gz"
            ])
            .add_local_python_source("train"))

volume = modal.Volume.from_name("meld-data", create_if_missing=True)
modal_volume = modal.Volume.from_name("meld-model", create_if_missing=True)

@app.function(
    image=image,
    gpu="A10G", 
    volumes={"/data": volume, "/models": modal_volume}, 
    timeout=60 * 60 * 24
)
def train_modal():
    train()

@app.local_entrypoint()
def main():
    train_modal.remote()