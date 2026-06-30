"""
tests/evaluate_pipeline.py

Pipeline evaluation script for measuring:
- latency
- retrieval similarity
- grounding overlap

Outputs evaluation metrics for report analysis.
"""

import sys
import os
import csv
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_pipeline import run_pipeline

TEST_URLS = [
    "https://www.nike.com",
    "https://www.apple.com",
    "https://www.redbull.com",
    "https://www.tesla.com",
    "https://streamlit.io",
]


def jaccard(text_a: str, text_b: str) -> float:
    a = set(text_a.lower().split())
    b = set(text_b.lower().split())
    if not a or not b:
        return 0.0
    return round(len(a & b) / len(a | b), 4)


def evaluate():
    results = []

    for url in TEST_URLS:
        print(f"\nEvaluating: {url}")
        try:
            result = run_pipeline(url, force_refresh=True)

            if not result["success"]:
                print(f"  FAILED: {result['error']}")
                results.append({
                    "url": url, "status": "FAILED",
                    "latency_s": 0, "chunks": 0,
                    "avg_similarity": 0, "jaccard": 0,
                    "taglines": "", "error": result["error"]
                })
                continue

            parsed     = result["parsed_output"]
            taglines   = parsed.get("taglines", [])
            raw        = result.get("raw_response", "")
            tagline_text = " ".join(taglines)

            row = {
                "url":            url,
                "status":         "OK",
                "brand":          result["brand_assets"]["brand_name"],
                "tone":           result["brand_assets"]["tone"],
                "latency_s":      result["latency"],
                "chunks":         result["chunks_used"],
                "avg_similarity": result.get("avg_similarity", 0),
                "jaccard":        jaccard(raw, tagline_text),
                "taglines":       " | ".join(taglines),
                "error":          ""
            }
            results.append(row)

            print(f"  Brand:    {row['brand']}")
            print(f"  Latency:  {row['latency_s']}s")
            print(f"  Taglines: {taglines}")

        except Exception as e:
            print(f"  EXCEPTION: {e}")
            results.append({
                "url": url, "status": "EXCEPTION",
                "latency_s": 0, "chunks": 0,
                "avg_similarity": 0, "jaccard": 0,
                "taglines": "", "error": str(e)
            })

    # Save CSV
    os.makedirs("data", exist_ok=True)
    csv_path = "data/evaluation_results.csv"
    fieldnames = ["url", "status", "brand", "tone", "latency_s",
                  "chunks", "avg_similarity", "jaccard", "taglines", "error"]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Results saved to {csv_path}")

    # Summary
    ok = [r for r in results if r["status"] == "OK"]
    if ok:
        avg_lat = sum(r["latency_s"] for r in ok) / len(ok)
        avg_sim = sum(r["avg_similarity"] for r in ok) / len(ok)
        print(f"\n📊 Summary ({len(ok)}/{len(results)} succeeded):")
        print(f"   Avg latency:    {avg_lat:.1f}s")
        print(f"   Avg similarity: {avg_sim:.3f}")


if __name__ == "__main__":
    evaluate()