#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
    Title: tax_sofrware.py
    Date: 2021-03-16
    Author: Yuexin Yu
    
    Description:
        A web app to get the taxon or taxid from the user, search in the 
        constructed database parsed from ncbi taxonomy, and output the taxon
        path. 
        
    List of functions:
        find_lineage,
        lineage_generator,
        taxonomy_dic_generator,
        work_flow,
        main_page,
        taxon_path_output  
        
    List of "non standard" modules:
        flask,
        json
        
    Procedure:
        1. Get the taxon or taxid from the user
        2. Search in the constructed database parsed from ncbi taxonomy
            If the databse is not generated in the local, it will do it first
        3. Output the taxon path
        
    Usage:
        python tax_sofrware.py
'''

from flask import Flask, render_template, request
import json
import os


app = Flask(__name__)


def find_lineage(parent_id, db):
    '''
    The function find the scientifc name of given taxid and update parent id as its parent id. 
    Parameters
    ----------
    parent_id : STR
        The parent id passed from lineage_generator function, the taxid used in this function.
    db : DICT{STR:STR/[STR]/{STR:STR}}
        The database in dictionary used in this script.

    Returns
    -------
    name : STR
        The scientific name of current taxid.
    new_parent_id : STR
        The parent id for current taxid.
    terminate_flag : INT
        0 in default. 1 if the rank goes to the highest rank ('superkingdom').

    '''
    terminate_flag = 0
    name = ''
    if db[parent_id]['rank'].lower().strip() == 'superkingdom':
        terminate_flag = 1
    for tax_id, infor in db.items():
        if tax_id == parent_id:
            for nameClass, nameText in infor['names'].items():
                if nameClass.replace(' ', '').lower() == 'scientificname':
                    name = nameText[0]
                    new_parent_id = db[tax_id]['parent_tax_id']
    return name, new_parent_id, terminate_flag 


def lineage_generator(parent_id, db):
    '''
    This function uses parent id passed from function taxonomy_dic_generator and output its lineage in a given format 
    Parameters
    ----------
    parent_id : STR
        The parent id of the taxid that is working on in function taxonomy_dic_generator.
    db : DICT{STR:STR/[STR]/{STR:STR}}
        The database in dictionary used in this script.

    Returns
    -------
    result : STR
        The lineage of given taxid separated by ';'.

    '''
    result = ''
    current_name = ''
    terminate_flag = 0
    new_parent_id = parent_id
    while terminate_flag != 1: # loop until the current parent id's rank is the highest
        current_name, new_parent_id, terminate_flag = find_lineage(new_parent_id, db)
        result  = current_name + '; ' + result
    return result
    
     
def taxonomy_dic_generator(taxid, db):
    '''
    The function generates the taxon path of given taxid.

    Parameters
    ----------
    taxid : STR
        The tax id that is look for taxon path.
    db : DICT{STR:STR/[STR]/{STR:STR}}
        The database in dictionary used in this script.

    Returns
    -------
    result : DICT{STR:{STR:STR}}
        The taxon path of given tax id.

    '''
    parent_id = db[taxid]['parent_tax_id']
    
    # Get the raxon path from the information from the database (db)
    result = {}
    result['taxid'] = taxid
    result['scientificName'] = db[taxid]['names']['scientific name'][0]
    if 'genbank common name' in db[taxid]['names']:
        result['commonName'] = db[taxid]['names']['genbank common name'][0]
        result['formalName'] = 'true'
    elif 'common name' in db[taxid]['names']:
        result['commonName'] = db[taxid]['names']['common name'][0]
        result['formalName'] = 'false'
    result['rank'] = db[taxid]['rank']
    result['division'] = db[taxid]['division']
    result['lineage'] = lineage_generator(parent_id, db)
    result['geneticCode'] = db[taxid]['geneticCode']
    result['mitochondrialGeneticCode'] = db[taxid]['mitochondrialGeneticCode']
    result['submittable'] = ''
    return result
    ##### to be added here "submittable"

def work_flow(inpt):
    '''
    The function recognizes the input (either a list or a simple taxid 
    or taxon) is a tax id or a taxon and get the corresponding taxon path 
    and output as a list of dictionary

    Parameters
    ----------
    inpt : STR
        Input can be:
            1. A taxid
            2. A taxon
            3. A list of taxid or/and taxon (separated by ,).

    Returns
    -------
    op_taxonomy : LIST
        A list of dictionary of taxon path.

    '''
    # Make sure database infor is there
    if os.path.exists('ncbi_tax/db.json'):
        pass
    else:
        os.system('python db_preparation.py')
        
    # Generate division names list
    div_lst = []
    with open('ncbi_tax/div_list', 'r') as div:
        for d in div:
            div_lst.append(d)
    # Generate genCode names list
    gc_lst = []
    with open('ncbi_tax/gc_list', 'r') as gc:
        for g in gc:
            gc_lst.append(g)
            
        
    # Input can be:
    # 1. A taxid
    # 2. A taxon
    # 3. A list of taxid or/and taxon (separated by ,)
    
    # Get a list of unique input
    ip = list(set(inpt.split(',')))
    
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
                
    return op_taxonomy

    
@app.route('/') # function decorator
def main_page():
    '''
    The function render hello_template.html as a main page of this application 
    using flask package.
    '''
    return render_template('hello_template.html')

@app.route('/', methods=['POST'])
def taxon_path_output():
    '''
    The function runs function work_flow with input from the main page and 
    output in a format.
    '''
    inpt = request.form['input']
    p=[]
    ti = work_flow(inpt)
    ct = 1
    for i in ti:
        if ct == 1:
            p.append('<pre>[{')
        else:
            p.append('<pre>{')
        for k,v in i.items():
            p.append('&nbsp;&nbsp;'+k+' : '+v)
        if ct < len(ti):
            p.append('}</pre>')
        else:
            p.append('}]</pre>')
        ct += 1
    return '\n'.join(p)

if __name__ == '__main__':
    app.run()
