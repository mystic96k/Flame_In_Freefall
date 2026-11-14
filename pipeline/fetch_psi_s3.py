"""Explora y descarga archivos del bucket público de PSI en AWS (s3://nasa-psi).

No necesitas cuenta de AWS (acceso anónimo). OJO: el registro de AWS describe
ese bucket como datos de DSI y OASIS (materiales / materia blanda), así que
puede que NO tenga combustión. Por eso este script primero LISTA y filtra por
palabras clave; las Experiment Tables de combustión se descargan del portal
psi.nasa.gov (ver README).

Uso:
    python -m pipeline.fetch_psi_s3 --list                 # carpetas de primer nivel
    python -m pipeline.fetch_psi_s3 --find combustion flame bass flex
    python -m pipeline.fetch_psi_s3 --get "RUTA/archivo.csv"
"""
from __future__ import annotations

import argparse

from config.settings import RAW_PSI_DIR

BUCKET = "nasa-psi"
REGION = "us-west-2"


def client():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    return boto3.client("s3", region_name=REGION, config=Config(signature_version=UNSIGNED))


def list_top() -> list[str]:
    resp = client().list_objects_v2(Bucket=BUCKET, Delimiter="/")
    return [p["Prefix"] for p in resp.get("CommonPrefixes", [])]


def find(keywords: list[str], limit: int = 200) -> list[tuple[str, int]]:
    kws = [k.lower() for k in keywords]
    hits: list[tuple[str, int]] = []
    paginator = client().get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if any(k in key.lower() for k in kws):
                hits.append((key, obj["Size"]))
                if len(hits) >= limit:
                    return hits
    return hits


def get(key: str) -> str:
    dest = RAW_PSI_DIR / key.split("/")[-1]
    client().download_file(BUCKET, key, str(dest))
    print(f"Descargado en {dest}")
    return str(dest)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--find", nargs="+")
    ap.add_argument("--get")
    a = ap.parse_args()
    if a.list:
        for p in list_top():
            print(p)
    elif a.find:
        hits = find(a.find)
        for k, s in hits:
            print(f"{s / 1e6:8.2f} MB  {k}")
        if not hits:
            print("Sin coincidencias. Descarga las Experiment Tables desde psi.nasa.gov (ver README).")
    elif a.get:
        get(a.get)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
