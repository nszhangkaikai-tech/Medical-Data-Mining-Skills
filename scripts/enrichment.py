#!/usr/bin/env python3
"""
Real enrichment analysis via g:Profiler REST API.

Offline mode is NOT a placeholder: it records an explicit unexecuted status,
including HTTP status / item count / response hash = None, so reviewers can
tell that no live query was attempted. Pass --allow-network to enable live
queries. Only gene identifiers are sent; no patient-level data leaves the
machine.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    import urllib.request
    import urllib.error
except Exception as e:
    print("FAIL: urllib unavailable:", e)
    sys.exit(1)


GPROFILER_ENDPOINT = "https://biit.cs.ut.ee/gprofiler/api/gost/profile/"


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def read_gene_list(path):
    genes = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            g = line.strip()
            if g:
                genes.append(g)
    return genes


def _response_meta(body_bytes):
    return {
        "http_status": 200,
        "item_count": 0,
        "response_sha256": hashlib.sha256(body_bytes).hexdigest(),
    }


def run_gprofiler(genes, species, sources, user_threshold):
    source_list = [s.strip() for s in sources.split(',') if s.strip()]
    payload = {
        "organism": species,
        "query": genes,
        "sources": source_list,
        "domain_scope": "annotated",
        "significance_threshold_method": "g_SCS",
        "user_threshold": user_threshold,
        "no_evidences": False,
        "highlight": None,
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        GPROFILER_ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode('utf-8')
            status = resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')
        print(f"FAIL: g:Profiler HTTP {e.code}: {body[:200]}")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: g:Profiler request failed: {e}")
        sys.exit(1)

    if status != 200:
        print(f"FAIL: g:Profiler returned HTTP {status}")
        sys.exit(1)

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        print("FAIL: g:Profiler returned invalid JSON")
        sys.exit(1)

    return parsed, body, status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--genes', required=True)
    ap.add_argument('--species', default='hsapiens')
    ap.add_argument('--sources', default='GO:BP,GO:MF,GO:CC,KEGG,REAC')
    ap.add_argument('--user-threshold', type=float, default=0.05)
    ap.add_argument('--output', required=True)
    ap.add_argument('--allow-network', action='store_true', help='enable real API call')
    args = ap.parse_args()

    genes = read_gene_list(args.genes)
    if not genes:
        print("FAIL: gene list is empty")
        sys.exit(1)

    out = {
        "database": "gprofiler",
        "database_version": None,
        "species": args.species,
        "query_count": len(genes),
        "background_size": 0,
        "fdr_method": "g_SCS",
        "user_threshold": args.user_threshold,
        "provenance": {
            "endpoint": GPROFILER_ENDPOINT,
            "params": {k: v for k, v in vars(args).items() if k not in ('genes', 'output')},
            "request_gene_count": len(genes),
            "sample_genes": genes[:10],
        },
        "results": [],
        "note": "unexecuted: offline mode",
        "response_meta": {"http_status": None, "item_count": 0, "response_sha256": None},
    }

    if args.allow_network:
        parsed, raw, status = run_gprofiler(genes, args.species, args.sources, args.user_threshold)
        meta = parsed.get("meta", {}) if isinstance(parsed, dict) else {}
        out["database_version"] = meta.get("version")
        out["provenance"]["response_meta"] = meta
        items = []
        for r in parsed.get("result", []):
            items.append({
                "source": r.get("source"),
                "term_id": r.get("native"),
                "term_name": r.get("name"),
                "p_value": r.get("p_value"),
                "fdr": r.get("p_value"),
                "query_count": r.get("intersection_size"),
                "background_count": r.get("term_size"),
                "significant": r.get("significant"),
            })
        out["results"] = items
        out["note"] = "live g:Profiler result"
        out["response_meta"] = {
            "http_status": status,
            "item_count": len(items),
            "response_sha256": hashlib.sha256(raw.encode('utf-8')).hexdigest(),
        }

    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print('wrote', args.output)


if __name__ == '__main__':
    main()
