#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 18:32:21 2021

@author: yuexinyu
"""
import json
import os


os.system('wget https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz')
os.system('mkdir ncbi_tax')
os.system('tar -xzvf taxdump.tar.gz -f ncbi_tax/')

with open('ncbi_tax/names.dmp', 'r') as names:
    names_dmp = {}
    for line in names:
        taxid = line.split('|')[0].strip()
        name_text = line.split('|')[1].strip()
        unique_name = line.split('|')[2].strip()
        name_class = line.split('|')[3].strip()
        if taxid not in names_dmp:
            names_dmp[taxid] = {}
        if name_class not in names_dmp[taxid]:
            names_dmp[taxid][name_class] = []
            names_dmp[taxid][name_class.replace(' ', '_')+'_unique_name'] = []
        names_dmp[taxid][name_class].append(name_text)
        names_dmp[taxid][name_class.replace(' ', '_')+'_unique_name'].append(unique_name)
                    

with open('ncbi_tax/nodes.dmp', 'r') as nd:
    nodes_dmp = {}
    for line in nd:
        line_lst = line.split('|')
        taxid = line_lst[0].strip()
        if taxid not in nodes_dmp: # 
            nodes_dmp[taxid] = {}
        nodes_dmp[taxid]['parent_tax_id'] = line_lst[1].strip()
        nodes_dmp[taxid]['rank'] = line_lst[2].strip()
        nodes_dmp[taxid]['emblCode'] = line_lst[3].strip() # locus name prefix; not unique
        nodes_dmp[taxid]['division'] = line_lst[4].strip()
        nodes_dmp[taxid]['inherited_div_flag'] = line_lst[5].strip() # 1 if node inherits division from parent
        nodes_dmp[taxid]['geneticCode'] = line_lst[6].strip()
        nodes_dmp[taxid]['inherited_GC_flag'] = line_lst[7].strip() # 1 if node inherits genetic code from parent
        nodes_dmp[taxid]['mitochondrialGeneticCode'] = line_lst[8].strip()
        nodes_dmp[taxid]['inherited_MGC_flag'] = line_lst[9].strip() # 1 if node inherits mito gencode from parent
        nodes_dmp[taxid]['GenBank_hidden_flag'] = line_lst[10].strip() # 1 if name is suppressed in GenBank entry lineage
        nodes_dmp[taxid]['hidden_subtree_root_flag'] = line_lst[11].strip() # 1 if this subtree has no sequence data yet
# nodes_dmp = { id: { 'rank': } }
    
div_lst = []
with open('ncbi_tax/division.dmp', 'r') as div:
    for line in div:
        divId = line.split('|')[0].strip()
        divName = line.split('|')[1].strip()
        for k,v in nodes_dmp.items():
            nodes_dmp[k]['names'] = names_dmp[k] 
            # nodes_dmp = { id: { 'rank': '', 'names': { 'scitific name':[] } } }
            if nodes_dmp[k]['division'] == divId:
                nodes_dmp[k]['division'] = divName
        div_lst.append(divName.upper())
        div_lst.append(line.split('|')[2].strip().upper())
        
with open('ncbi_tax/div_list', 'w') as dl:
    for i in div_lst:
        dl.write(i+'\n')

with open('ncbi_tax/merged.dmp', 'r') as mer:
    for line in mer:
        old_taxid = line.split('|')[0].strip()
        new_taxid = line.split('|')[1].strip()
        if new_taxid in nodes_dmp:
            nodes_dmp[new_taxid]['old_taxid'] = old_taxid
            # nodes_dmp = { id: { 'rank': '', 'names': { 'scitific name':[] }, 'old_taxid': '' } }
        else:
            nodes_dmp[new_taxid]['old_taxid'] = ''

with open('ncbi_tax/delnodes.dmp', 'r') as delete:
    for line in delete:
        del_taxid = line.split('|')[0].strip()
        nodes_dmp[del_taxid] = {}
        
        
# Save the totoal divtionary information into file
with open('ncbi_tax/db.json', 'w') as db:
    db.write(json.dumps(nodes_dmp))
        
    
gc_lst = []
with open('ncbi_tax/gencode.dmp', 'r') as gc:
    for line in gc:
        gc_lst.append(line.split('|')[2].strip().upper())

with open('ncbi_tax/gc_list', 'w') as gl:
    for i in gc_lst:
        gl.write(i+'\n')
        
    
            
    

    
    
    
    
    
    
    