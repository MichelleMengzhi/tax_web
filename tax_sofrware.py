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
    new_parent_id = db[parent_id]['parent_tax_id'] # Save the parent id for the current taxid
    if db[parent_id]['rank'].lower().strip() == 'superkingdom' or db[parent_id]['rank'].lower().strip() == 'no rank':
        terminate_flag = 1
    if db[parent_id]['GenBank_hidden_flag'] != '1': # Only if GenBank hidden flag is 0 , the taxid will be added into the lineage
        for tax_id, infor in db.items():
            if tax_id == parent_id:
                for nameClass, nameText in infor['names'].items():
                    if nameClass.replace(' ', '').lower() == 'scientificname':
                        name = nameText[0] # Find the scientific name of the given taxid
                        break
                break
    
    
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
        if current_name != '':
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
    else: # neither genebank bommon name or common name is there
        result['formalName'] = 'false'
    result['rank'] = db[taxid]['rank']
    result['division'] = db[taxid]['division']
    result['lineage'] = lineage_generator(taxid, db)
    result['geneticCode'] = db[taxid]['geneticCode']
    result['mitochondrialGeneticCode'] = db[taxid]['mitochondrialGeneticCode']
    if result['rank'] == 'species':
        result['submittable'] = 'true'
    else:
        result['submittable'] = 'false'
    return result


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
            div_lst.append(d.strip())
    # Generate genCode names list
    gc_lst = []
    with open('ncbi_tax/gc_list', 'r') as gc:
        for g in gc:
            gc_lst.append(g.strip())
    # Generate merged taxid dictionary
            
        
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
                op_taxonomy.append(taxonomy_dic_generator(tax, db))
            else: # taxid is not in the database
                flag = 0
                with open('ncbi_tax/deletedtaxid', 'r') as deleted:
                    for line in deleted:
                        if tax == line.strip(): # indicate taxid is deleted
                            flag = 1
                            print('Given taxid '+str(tax)+' is deleted, no taxonomy information provided.')
                if flag != 1:  # indicate the given taxid is not deleted           
                    with open('ncbi_tax/merge_dic.json', 'r') as md:
                        merge_dic = json.load(md)
                    if tax in merge_dic: # merge case
                        taxid = merge_dic[tax]
                        op_taxonomy.append(taxonomy_dic_generator(taxid, db))
                    else:
                        print('Given taxid '+str(tax)+' does not exist.')
                   
        
        elif tax.replace(' ', '').upper() in div_lst: # indicate the given taxon is a division
            if len(tax) == 3:
                div = div_lst[div_lst.index(tax.upper())+1]
            else: 
                div = tax.replace(' ','').upper()
            with open('ncbi_tax/'+div+'.json', 'r') as divd:
                div_dic = json.load(divd)
            for k,v in div_dic.items():
                for i in v:
                    op_taxonomy.append(taxonomy_dic_generator(i, db))
        
        elif tax.replace(' ', '').upper() in gc_lst: # indicate the given taxon is a gene code name
            with open('ncbi_tax/'+tax.replace(' ', '').upper()+'.json', 'r') as gc:
                gc_dic = json.load(gc)
            if len(gc_dic) != 0: # skip the case that the file is empty, i.e there is no coppresonding txid for this gc name              
                for k,v in gc_dic.items():
                    for i in v:
                        op_taxonomy.append(taxonomy_dic_generator(i, db))
                
        else: # input is a name
            with open('ncbi_tax/names.json', 'r') as njs:
                names_dic = json.load(njs)
            if tax.replace(' ', '').upper() in names_dic:
                taxid = names_dic[tax.replace(' ', '').upper()]
                op_taxonomy.append(taxonomy_dic_generator(taxid, db))
            else:
                print('No match for given taxon '+str(tax))
                
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
    if len(ti) == 0:
        p.append('<pre>Given input does not have corresponding taxon path<br>This may be caused by: <br>The input taxid is deleted<br>The input taxon does not match any name, division name, or gencode name<br>The input taxon is a gencode name without any corresponding taxon id</pre>')
    else:
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
