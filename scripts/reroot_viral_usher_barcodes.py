"""Build Freyja barcodes from a viral_usher tree, expressed relative to CY121680.1.

The viral_usher tree's reference is a treetime-rerooted ancestral sequence that is
only ~81% identical to modern pdm09 H1N1 HA, so reads cannot be aligned to it.
matUtils cannot reroot a tree whose root carries mutations, so instead we take the
clade genotypes from `matUtils extract -C` (relative to the tree reference) and
re-express each one as differences from CY121680.1 (same reference as H1N1/).
Mutation positions use the full CY121680.1 record (UTRs included).

usage: reroot_viral_usher_barcodes.py lineagePaths.txt tree_ref.fa CY121680.1.fa out_prefix
       writes <out_prefix>.csv and <out_prefix>.feather
"""
import os
import re
import sys

import pandas as pd
from freyja.convert_paths2barcodes import (check_mutation_chain,
                                           convert_to_barcodes,
                                           parse_tree_paths,
                                           reversion_checking)

paths, treeref, cyfa, prefix = sys.argv[1:5]


def read_fasta(p):
    return ''.join(l.strip() for l in open(p)
                   if not l.startswith('>')).upper()


ref, cy = read_fasta(treeref), read_fasta(cyfa)
off = cy.find('ATGAAGGC')  # CDS start in the full record (0-based)
cds = cy[off:off + len(ref)]
assert off >= 0 and len(cds) == len(ref)

df = pd.read_csv(paths, sep='\t')
rows = []
for clade, p in zip(df['clade'], df['from_tree_root'].fillna('')):
    geno = {int(pos): alt for pos, alt in
            re.findall(r'[A-Z](\d+)([A-Z])', p.replace('>', ','))}
    diffs = [f'{cds[pos - 1]}{pos + off}{alt}' for pos, alt in geno.items()
             if alt in 'ACGT' and cds[pos - 1] != alt]
    # sites never mutated on the path carry the tree reference allele
    diffs += [f'{c}{i + off}{r}' for i, (r, c) in enumerate(zip(ref, cds), 1)
              if i not in geno and r != c]
    diffs.sort(key=lambda x: int(x[1:-1]))
    rows.append((clade, ' > '.join(diffs)))

d = parse_tree_paths(pd.DataFrame(rows, columns=['clade', 'from_tree_root']))
b = check_mutation_chain(reversion_checking(convert_to_barcodes(d)))
b.to_csv(prefix + '.csv')
b.reset_index().to_feather(prefix + '.feather')
print(f'{b.shape[0]} lineages x {b.shape[1]} mutations', file=sys.stderr)
