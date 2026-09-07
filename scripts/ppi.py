#!/usr/bin/env python3
"""
Real PPI network via STRING REST API.

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
    import urllib.parse
    import urllib.request
    import urllib.error
except Exception as e:
    print("FAIL: urllib unavailable:", e)
    sys.exit(1)


STRING_ENDPOINT = "https://string-db.org/api/json/network"


def read_gene_list(path):
    genes = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            g = line.strip()
            if g:
                genes.append(g)
    return genes


def run_string(genes, species, score_threshold):
    params = {
        "identifiers": "%0d".join(genes),
        "species": species,
        "required_score": score_threshold,
        "add_nodes": "0",
        "show_query_node_names": "1",
    }
    url = STRING_ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode('utf-8')
            status = resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')
        print(f"FAIL: STRING HTTP {e.code}: {body[:200]}")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: STRING request failed: {e}")
        sys.exit(1)

    if status != 200:
        print(f"FAIL: STRING returned HTTP {status}")
        sys.exit(1)

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        print("FAIL: STRING returned invalid JSON")
        sys.exit(1)

    return parsed, body, status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--genes', required=True)
    ap.add_argument('--species', type=int, default=9606)
    ap.add_argument('--score-threshold', type=int, default=400)
    ap.add_argument('--output', required=True)
    ap.add_argument('--allow-network', action='store_true', help='enable real API call')
    args = ap.parse_args()

    genes = read_gene_list(args.genes)
    if not genes:
        print("FAIL: gene list is empty")
        sys.exit(1)

    out = {
        "database": "string",
        "database_version": None,
        "species": args.species,
        "score_threshold": args.score_threshold,
        "query_count": len(genes),
        "provenance": {
            "endpoint": STRING_ENDPOINT,
            "params": {k: v for k, v in vars(args).items() if k not in ('genes', 'output')},
            "request_gene_count": len(genes),
            "sample_genes": genes[:10],
        },
        "nodes": [{"gene": g, "type": "input"} for g in genes],
        "edges": [],
        "note": "unexecuted: offline mode",
        "response_meta": {"http_status": None, "item_count": 0, "response_sha256": None},
    }

    if args.allow_network:
        parsed, raw, status = run_string(genes, args.species, args.score_threshold)
        node_ids = set()
        edges = []
        for interaction in parsed:
            node1 = interaction.get("preferredName_A")
            node2 = interaction.get("preferredName_B")
            score = interaction.get("score")
            if node1:
                node_ids.add(node1)
            if node2:
                node_ids.add(node2)
            edges.append({
                "source": node1,
                "target": node2,
                "score": score,
                "database": "string",
            })
        out["database_version"] = parsed[0].get("stringdb_version") if parsed else None
        out["nodes"] = [{"gene": g, "type": "input"} for g in sorted(node_ids)]
        out["edges"] = edges
        out["note"] = "live STRING result"
        out["response_meta"] = {
            "http_status": status,
            "item_count": len(edges),
            "response_sha256": hashlib.sha256(raw.encode('utf-8')).hexdigest(),
        }

    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print('wrote', args.output)


if __name__ == '__main__':
    main()
