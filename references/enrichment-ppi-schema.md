# Enrichment / PPI Schema

## enrichment_results.json
{
  "database": "string_biogrid | go | kegg | reactome",
  "database_version": "yyyy-mm-dd",
  "background_genes": 20000,
  "method": "ORA | GSEA | hypergeom",
  "fdr_method": "BH | Bonferroni | q-value",
  "results": [
    {
      "gene": "TP53",
      "term_id": "GO:0006915",
      "term_name": "apoptotic process",
      "p_value": 0.0123,
      "fdr": 0.0456,
      "hits": 3
    }
  ]
}

## ppi_results.json
{
  "database": "string_biogrid | intact | biogrid",
  "database_version": "yyyy-mm-dd",
  "nodes": [
    {"gene": "TP53", "type": "input"}
  ],
  "edges": [
    {
      "source": "TP53",
      "target": "MDM2",
      "score": 0.9,
      "evidence": "experimental | database | textmining"
    }
  ]
}
