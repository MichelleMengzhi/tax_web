#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
    Title: db_preparation.py
    Date: 2021-03-16
    Author: Yuexin Yu
    
    Description:
        The script to prepare a dtdbase using data from NCBI taxonomy databse.
        
    List of functions:
        \ 
        
    List of "non standard" modules:
        json
        
    Procedure:
        1. Install the latest version of NCBI taxonomy database
        2. Open needed database ans parse data
            2.1 Parse name information from names.dmp
            2.2 Parse taxid corrsponding information from nodes.dmp to generate 
            a new dictionary saving taxid as key and information as value as a 
            new database, as well as save genetic code corresponding taxids and 
            division code corresponding taxids separately
            2.3 Parse division name and save into corresponding taxids' 
            information from divisions.dmp, as well as make a dictionary with 
            division name as key and correpsonding taxids as value
            2.4 Parse merged taxid and save into corresponding taxids from 
            merged.dmp, as well as save a merged_taxid:corresponding_new_taxid 
            dictionary for searching
            2.5 Parse deleted taxid and save into the new database.
            2.6 Parse genetic code name from gencode.dmp as a list for searching,
            as well as make a dictionary with genecode name as key and 
            corresponding taxids as value 
        3. Save new generated database, dictionaries, and list into corresponding 
        files
        
    Usage:
        python db_preparation.py
'''
import json
import os


os.system('wget https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz')
os.system('mkdir ncbi_tax')
os.system('tar -xzvf taxdump.tar.gz -C ncbi_tax/')


with open('ncbi_tax/names.dmp', 'r') as names, \
    open('ncbi_tax/names.json', 'w') as njs:
    names_dmp = {}
    names_dic = {}
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
        names_dic[name_text.replace(' ', '').upper()] = taxid
    njs.write(json.dumps(names_dic))
    
                
gc_lst = {} # The dictionary storing genetic code as key, corresponding taxid as value
div_lst = {} # The dictionary storing division code as key, corresponding taxid as value
with open('ncbi_tax/nodes.dmp', 'r') as nd:
    nodes_dmp = {} # The dictionary storing taxid as key, corresponding data as value
    for line in nd:
        line_lst = line.split('|')
        taxid = line_lst[0].strip()
        if taxid not in nodes_dmp: # 
            nodes_dmp[taxid] = {}
        if line_lst[6].strip() not in gc_lst:
            gc_lst[line_lst[6].strip()] = []   
        if line_lst[4].strip() not in div_lst:
            div_lst[line_lst[4].strip()] = []
        nodes_dmp[taxid]['parent_tax_id'] = line_lst[1].strip()
        nodes_dmp[taxid]['rank'] = line_lst[2].strip()
        #nodes_dmp[taxid]['emblCode'] = line_lst[3].strip() # locus name prefix; not unique
        nodes_dmp[taxid]['division'] = line_lst[4].strip()
        #nodes_dmp[taxid]['inherited_div_flag'] = line_lst[5].strip() # 1 if node inherits division from parent
        nodes_dmp[taxid]['geneticCode'] = line_lst[6].strip()
        #nodes_dmp[taxid]['inherited_GC_flag'] = line_lst[7].strip() # 1 if node inherits genetic code from parent
        nodes_dmp[taxid]['mitochondrialGeneticCode'] = line_lst[8].strip()
        #nodes_dmp[taxid]['inherited_MGC_flag'] = line_lst[9].strip() # 1 if node inherits mito gencode from parent
        nodes_dmp[taxid]['GenBank_hidden_flag'] = line_lst[10].strip() # 1 if name is suppressed in GenBank entry lineage
        #nodes_dmp[taxid]['hidden_subtree_root_flag'] = line_lst[11].strip() # 1 if this subtree has no sequence data yet
        gc_lst[line_lst[6].strip()].append(taxid)
        div_lst[line_lst[4].strip()].append(taxid)
# nodes_dmp = { id: { 'rank': } }
    

with open('ncbi_tax/division.dmp', 'r') as div, \
    open('ncbi_tax/div_list', 'w') as dl:
        for line in div:
            div_dic = {}
            divId = line.split('|')[0].strip()
            divName = line.split('|')[1].strip()
            for k,v in nodes_dmp.items():
                nodes_dmp[k]['names'] = names_dmp[k] 
                # nodes_dmp = { id: { 'rank': '', 'names': { 'scitific name':[] } } }
                if nodes_dmp[k]['division'] == divId:
                    nodes_dmp[k]['division'] = divName
            dl.write(divName.upper()+'\n')
            dl.write(line.split('|')[2].strip().replace(' ', '').upper()+'\n')
            div_dic[divName] = div_lst[divId]
            with open('ncbi_tax/'+line.split('|')[2].strip().replace(' ','').upper()+'.json', 'w') as fl:
                fl.write(json.dumps(div_dic))
            
        
merge_dic = {}
with open('ncbi_tax/merged.dmp', 'r') as mer:
    for line in mer:
        old_taxid = line.split('|')[0].strip()
        new_taxid = line.split('|')[1].strip()
        merge_dic[old_taxid] = new_taxid
        if new_taxid in nodes_dmp:
            nodes_dmp[new_taxid]['old_taxid'] = old_taxid
            # nodes_dmp = { id: { 'rank': '', 'names': { 'scitific name':[] }, 'old_taxid': '' } }
        else:
            nodes_dmp[new_taxid]['old_taxid'] = ''
  
            
with open('ncbi_tax/merge_dic.json', 'w') as mer_dic:
    mer_dic.write(json.dumps(merge_dic))          
            

with open('ncbi_tax/delnodes.dmp', 'r') as delete,\
    open('ncbi_tax/deletedtaxid', 'w') as dele:
        for line in delete:
            del_taxid = line.split('|')[0].strip()
            dele.write(del_taxid+'\n')
        
        
# Save the totoal divtionary information into file
with open('ncbi_tax/db.json', 'w') as db:
    db.write(json.dumps(nodes_dmp))
        
    
with open('ncbi_tax/gencode.dmp', 'r') as gc, \
    open('ncbi_tax/gc_list', 'w') as gl:
        for line in gc:
            gc_dic = {}
            gc_code = line.split('|')[0].strip()
            gc_name = line.split('|')[2].strip().replace(' ', '').upper().split(';')
            for i in gc_name:
                gl.write(i.strip()+'\n')
                if gc_code in gc_lst:
                    gc_dic[i] = gc_lst[gc_code]
                    with open('ncbi_tax/'+i+'.json', 'w') as file:
                        file.write(json.dumps(gc_dic))
                else:
                    with open('ncbi_tax/'+i+'.json', 'w') as file:
                        file.write(json.dumps({}))
        
    
            
    

    
    
    
    
    
    
    