import yaml
import pandas as pd

clade_info = pd.read_csv("https://raw.githubusercontent.com/nextstrain/mpox/refs/heads/master/phylogenetic/defaults/clades.tsv",sep='\t',skiprows=1)
clade_info = clade_info[clade_info['gene']=='clade']
clade_info = clade_info[['clade','site']]
cI = pd.DataFrame([['clade I','root']],columns=['clade','site'])
cII = pd.DataFrame([['clade II','root']],columns=['clade','site'])
clade_info = pd.concat([cI,cII,clade_info],axis=0,ignore_index=True)

#switch to freyja naming scheme
clade_info['clade'] = clade_info['clade'].apply(lambda x:x.replace('clade ',''))
clade_info['site'] = clade_info['site'].apply(lambda x:x.replace('clade ',''))
clade_info['clade'] = clade_info['clade'].apply(lambda x:'MPX-' + x if (x[0]=='I' or x=='root') else 'MPX-IIb.' + x )
clade_info['site'] = clade_info['site'].apply(lambda x:'MPX-' + x if (x[0]=='I' or x=='root') else 'MPX-IIb.' + x )

all_clades = clade_info['clade']
clade_info = clade_info.set_index('clade')

# add all descendants to that clade
def getDescendant(clade0):
    children = clade_info[clade_info['site']==clade0]
    if children.shape[0]>0:
        children = list(children.index)
        for c in children:
            c0 = getDescendant(c)
        children += c0
        return children
    else:
        return []

hierarchy = []
for clade in all_clades:
    h0 = {}
    h0['name'] = clade
    if 'Ia' in clade:
        h0['alias'] = clade.replace('Ia','I.a')
    elif 'Ib' in clade:
        h0['alias'] = clade.replace('Ib','I.b')
    else:
        h0['alias'] = clade
    if clade_info.loc[clade,'site'] != 'MPX-root':
        h0['parent'] = clade_info.loc[clade,'site']
    h0['children'] = getDescendant(clade) + [clade]
    hierarchy.append(h0)

with open('mpox_lineages.yml', 'w') as yaml_file:
    yaml.dump(hierarchy,yaml_file,sort_keys=False)

