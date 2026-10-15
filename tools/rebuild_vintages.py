"""Rebuild compact, versioned archive counts from pinned public CSV snapshots.

Ordinary reproduction uses the included compact data and needs no network.
This optional provenance check downloads about 1.5 GB uncompressed in total.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import hashlib
import io
import json
from pathlib import Path
import time
from urllib.request import urlopen, Request

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REGIONS = ["Cherkaska oblast", "Chernihivska oblast", "Chernivetska oblast", "Dnipropetrovska oblast", "Donetska oblast", "Ivano-Frankivska oblast", "Kharkivska oblast", "Khersonska oblast", "Khmelnytska oblast", "Kirovohradska oblast", "Kyiv City", "Kyivska oblast", "Luhanska oblast", "Lvivska oblast", "Mykolaivska oblast", "Odeska oblast", "Poltavska oblast", "Rivnenska oblast", "Sumska oblast", "Ternopilska oblast", "Vinnytska oblast", "Volynska oblast", "Zakarpatska oblast", "Zaporizka oblast", "Zhytomyrska oblast"]


def retrieve(entry, cache):
    path = cache / (entry["sha"] + ".csv.gz")
    if path.exists():
        raw = gzip.decompress(path.read_bytes())
    else:
        for attempt in range(3):
            try:
                with urlopen(Request(entry["url"], headers={"User-Agent":"KSE-reproducible-research"}), timeout=90) as response:
                    raw = response.read()
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        path.write_bytes(gzip.compress(raw, mtime=0))
    digest = hashlib.sha256(raw).hexdigest()
    if entry.get("sha256") and entry["sha256"] != digest:
        raise ValueError("Snapshot checksum mismatch: " + entry["sha"])
    df = pd.read_csv(io.BytesIO(raw), usecols=["region", "started_at"])
    before = len(df)
    df = df.drop_duplicates(["region", "started_at"])
    starts = pd.to_datetime(df.started_at, utc=True)
    stamp = pd.Timestamp(entry["committed_at"])
    if (starts > stamp).any():
        raise ValueError("Start after archive commit time: " + entry["sha"])
    df["date"] = starts.dt.tz_convert("Europe/Kyiv").dt.strftime("%Y-%m-%d")
    end = (stamp.tz_convert("Europe/Kyiv").normalize() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    dates = pd.date_range("2026-04-01", end).strftime("%Y-%m-%d")
    # Explicit target: records in a completely read snapshot, not true alerts.
    # Zero is a verified empty archive query; actual alert count remains unknown.
    index = pd.MultiIndex.from_product([dates, REGIONS], names=["date", "region"])
    counts = df.groupby(["date","region"]).size().reindex(index, fill_value=0).rename("archive_records").reset_index()
    counts.insert(0, "vintage", stamp.isoformat())
    metadata = {**entry, "sha256":digest, "input_rows":before,
                "unique_region_starts":len(df),"last_start_utc":str(starts.max()),
                "last_start_by_region":df.groupby("region").started_at.max().to_dict()}
    return counts, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT/"data/snapshot_manifest.json").read_text())
    frames, metadata = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(retrieve, entry, args.cache) for entry in manifest]
        for i, future in enumerate(as_completed(futures), 1):
            counts, record = future.result()
            frames.append(counts)
            metadata.append(record)
            if i % 10 == 0 or i == len(futures):
                print(f"Snapshots processed: {i}/{len(futures)}", flush=True)
    data = pd.concat(frames).sort_values(["vintage","date","region"])
    raw = data.to_csv(index=False, lineterminator="\n").encode()
    (ROOT/"data/vintage_counts.csv.gz").write_bytes(gzip.compress(raw, mtime=0))
    metadata.sort(key=lambda x:x["committed_at"])
    (ROOT/"data/snapshot_manifest.json").write_text(json.dumps(metadata,indent=2)+"\n",encoding="utf-8")
    (ROOT/"data/vintage_counts.sha256").write_text(hashlib.sha256(raw).hexdigest()+"\n")
    print(f"Done: {len(metadata)} snapshots, {len(data)} regional daily queries.", flush=True)


if __name__ == "__main__":
    main()
