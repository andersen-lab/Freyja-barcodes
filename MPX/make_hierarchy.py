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

clade_info['base'] = [ci.split('.')[1:] if '.' in ci else '' for ci in clade_info['site']]
clade_info['parent_base'] = [ci.split('.')[1:] if '.' in ci else '' for ci in clade_info.index]
key_extract = clade_info.copy()
key_extract = key_extract[key_extract['base'].apply(lambda x: len(x)>0)]
key_extract = key_extract[key_extract[['base','parent_base']].apply(lambda x: x['base'][0]!=x['parent_base'][0],axis=1)]
alias_key = {pb[0]:'.'.join(b) for b,pb in zip(key_extract['base'],key_extract['parent_base'])}

def getCompleteName(v):
    while v.split('.')[0] in alias_key.keys():
        v = alias_key[v.split('.')[0]] + '.'+ '.'.join(v.split('.')[1:])
        v = getCompleteName(v)
    return v

alias_key0 = {key:getCompleteName(val) for key,val in zip(alias_key.keys(),alias_key.values())}
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
    
def replace_values(string, replacements):
    for key, value in replacements.items():
        string = string.replace(key, value)
    return string

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
    
    h0['alias'] = replace_values(h0['alias'],alias_key0)
    if clade_info.loc[clade,'site'] != 'MPX-root':
        h0['parent'] = clade_info.loc[clade,'site']
    children = list(set(getDescendant(clade) + [clade]))
    children.sort()
    h0['children'] = children
    hierarchy.append(h0)

with open('mpox_lineages.yml', 'w') as yaml_file:
    yaml.dump(hierarchy,yaml_file,sort_keys=False)

