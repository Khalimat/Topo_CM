import pandas as pd


def signature_extractor(file):
    # preprocessing data before
    # calculating up/down regulated genes

    stat = pd.read_table(file, sep=" ")
    stat = stat.apply(pd.to_numeric)

    up_genes = []
    down_genes = []
    names = stat.columns
    stat = stat.sort_values(by=["logFC", "PValue"], ascending=[False, True])

    # calculating up/down regulated genes

    if names[0] == "logFC" and names[2] == "PValue":
        up_genes = stat[(stat["logFC"] >= 2) & (stat["PValue"] <= 1e-3)].index
        down_genes = stat[(stat["logFC"] <= -2) & (stat["PValue"] <= 1e-3)].index

    if names[1] == "log2FoldChange" and names[5] == "padj":
        up_genes = stat[(stat["log2FoldChange"] >= 2) & (stat["padj"] <= 1e-3)].index
        down_genes = stat[(stat["log2FoldChange"] <= -2) & (stat["padj"] <= 1e-3)].index

    return up_genes, down_genes
