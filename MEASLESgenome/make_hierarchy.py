import yaml
import pandas as pd
import re

df_barcodes = pd.read_csv("latest/barcode.csv",index_col=0)

all_lineages = list(df_barcodes.index)
all_lineages = [l.split('-')[1] for l in all_lineages if 'unassigned' not in l]

hierarchy = []
prefix = 'MEASLES'
for lin in all_lineages:
    h0 = {}
    h0['name'] = f"{prefix}-{lin}"
    if len(lin)>1:
        h0['alias'] = f"{prefix}-{lin[0]}.{lin[1:]}"
    else:
        h0['alias'] = f"{prefix}-{lin}"
    if len(h0['alias'].split('.'))>1:
        split = h0['alias'].split('.')
        h0['parent'] = '.'.join(split[0:(len(split)-1)])
    # h0['children'] = [f"{prefix}-{l}" for l in all_lineages if l.startswith(lin)]
    hierarchy.append(h0)

# if parent not in hierarchy, let's add it. 
for h in hierarchy:
    if ('parent' in h.keys()):
        if h['parent'] not in [h0['name'] for h0 in hierarchy]:
            # added_entry = []
            # for h0 in hierarchy:
            #     if ('parent' in h0.keys()):
            #         if (h['parent']==h0['parent']):
            #             added_entry.append(h0['name'])
            new_lin = {'name':h['parent'],
                    'alias':h['parent']}
                    # 'children':added_entry}
            hierarchy.append(new_lin)

### now handle the children, using aliases. 
for h0 in hierarchy:
    h0['children'] = [h['name'] for h in hierarchy if h['alias'].split('.')[0]==h0['name'] or h['name']==h0['name']]

with open('lineages.yml', 'w') as yaml_file:
    yaml.dump(hierarchy,yaml_file,sort_keys=False)
