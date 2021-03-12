#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 18:32:21 2021

@author: yuexinyu
"""

import os
import sys
# from tkinter import *
import json


def find_lineage(parent_id, db):
    terminate_flag = 0
    name = ''
    if db[parent_id]['rank'].lower().strip() == 'superkingdom':
        terminate_flag = 1
    for tax_id, infor in db.items():
        if tax_id == parent_id:
            for nameClass, nameText in infor['names'].items():
                if nameClass.replace(' ', '').lower() == 'scientificname':
                    name = nameText
                    new_parent_id = db[tax_id]['parent_tax_id']
    return name, new_parent_id, terminate_flag 


def lineage_generator(parent_id, db):
    result = ''
    current_name = ''
    terminate_flag = 0
    new_parent_id = parent_id
    while terminate_flag == 1:
        current_name, new_parent_id, terminate_flag = find_lineage(new_parent_id, db)
        result  = result + current_name + '; '
    return result
    
     
def taxonomy_dic_generator(taxid, db):
    parent_id = db[taxid]['parent_tax_id']

    result = {}
    result['taxid'] = taxid
    result['scientificName'] = db[taxid]['names']['scientific name']
    if 'genbank common name' in db[taxid]['names']:
        result['commonName'] = db[taxid]['names']['genbank common name']
        result['formalName'] = 'true'
    elif 'common name' in db[taxid]['names']:
        result['commonName'] = db[taxid]['names']['common name']
        result['formalName'] = 'false'
    result['rank'] = db[taxid]['rank']
    result['division'] = db[taxid]['divsion']
    result['lineage'] = lineage_generator(parent_id, db)
    result['geneticCode'] = db[taxid]['geneticCode']
    result['mitochondrialGeneticCode'] = db[taxid]['mitochondrialGeneticCode']
    result['submittable'] = ''
    ##### to be added here "submittable"


# Make sure database infor is there
if os.path.exists('ncbi_tax/db.json'):
    pass
else:
    os.system('python db_preparation.py')
    
# Generate division names list
div_lst = []
with open('ncbi_tax/div_lst', 'r') as div:
    for d in div:
        div_lst.append(d)
# Generate genCode names list
gc_lst = []
with open('ncbi_tax/gc_lst', 'r') as gc:
    for g in gc:
        gc_lst.append(g)
        
    
# Input can be:
# 1. A taxid
# 2. A taxon
# 3. A list of taxid or/and taxon (separated by ,)

# Get a list of unique input
ip = list(set(sys.argv[1].split(',')))

with open('ncbi_tax/db.json') as dbjson:
    db = json.load(dbjson) # Read database information

op_taxonomy = []
for tax in ip:
    tax = tax.strip()
    if tax.isdigit(): # indicates the element is a taxid
        if tax in db: # taxid is in the database taxids
            if db[tax] == {}: # indicates the given taxid does not have corresponding node information, i.e. a deleted taxid
                print('Given taxid '+str(tax)+' is deleted, no taxonomy information provided.')
            else: # indicates the given taxid is not deleted
                op_taxonomy.append(taxonomy_dic_generator(tax, db))
    
    elif tax.upper() in div_lst: # indicate the given taxon is a division
        if len(tax) != 3:
            div = div_lst[div_lst.index(tax.upper())-1]
        else: 
            div = tax.upper()
        for tid, info in db.items():
            if info['division'] == div:
                op_taxonomy.append(taxonomy_dic_generator(tid, db))
        div = ''
    
    elif tax.upper() in gc_lst: # indicate the given taxon is a gene code name
        gc = gc_lst.index(tax.upper())
        for tid, info in db.items():
            if info['geneticCode'] == gc or info['mitochondrialGeneticCode'] == gc: ### To be decided whether should be divided into 2 cases
                op_taxonomy.append(taxonomy_dic_generator(tid, db))
        gc = ''
            
    else: # input is a name
        find_id = 0
        for tid, info in db.items():
            for name_class, name_text in info['names'].items():
                if name_text.replace(' ', '').upper() == tax.replace(' ', '').upper(): # indicates the given taxon matches a name in this taxid
                    find_id = 1
                    op_taxonomy.append(taxonomy_dic_generator(tax, db))                  
        if find_id == 1:
            print('No match for given taxon '+tax)
            
    
                
    
    
    
    
    
    
    
    