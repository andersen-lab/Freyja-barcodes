import yaml
import pandas as pd
import numpy as np
import re

clade_info = list(pd.read_csv("latest/barcode.csv",index_col=0).index)

clade_full_names = [name.replace('-A','-2.3.4.4.b.A') if name!='H5Nx-Am-nonGsGD' else name for name in clade_info]

clade_full_names = [f"{name[0:len(name)-1]}.{name[-1]}" if name[-1].islower() else name for name in clade_full_names]

hierarchy = []
for clade,cladefn in zip(clade_info,clade_full_names):
    h0 = {}
    h0['name'] = clade
    h0['alias'] = cladefn
    h0['children'] = [cfn for cfn in clade_full_names if cfn.startswith(cladefn)]
    break0 = cladefn.split('.')
    put_parent = '.'.join(break0[0:len(break0)-1])
    if put_parent in clade_full_names:
        ind0 = clade_full_names.index(put_parent)
        h0['parent'] = clade_info[ind0]
    hierarchy.append(h0)

with open('lineages.yml', 'w') as yaml_file:
    yaml.dump(hierarchy,yaml_file,sort_keys=False)
