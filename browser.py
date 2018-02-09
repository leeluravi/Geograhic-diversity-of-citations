#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 10:35:02 2017

@author: leeluravi
This code works for Hardvard referencing style: Last name, First Initial. (Year published). Title. City: Publisher, Page(s).
The extracted text document has one term in each line.
The reference blocks are seperated by two blank lines.

"""
from  flask import Flask
from flask import render_template
import scholarly
#import coloredlogs, logging
import requests
import io
#from io import StringIO
#from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
#from pdfminer.converter import TextConverter
#from pdfminer.layout import LAParams
#from pdfminer.pdfpage import PDFPage
#import os
import sys
#import sys, getopt
from flask import json
import re 

geocodes = [];
locations=[];
line_cache = [];
publication_city = '';

# search function uses google service to obtain address
# search_term is the phrase being provided to the service to search in Google maps
# pubcity is boolean input which tells the function it is searching for a publication city or for author's affiliation
app = Flask(__name__);
def search(search_term, pubcity):
    GOOGLE_MAPS_API_URL = 'http://maps.googleapis.com/maps/api/geocode/json';
    params = {
        'address': search_term,
        'sensor': 'false'
    };
    
    # Do the request and get the response data
    req = requests.get(GOOGLE_MAPS_API_URL, params=params);
    res = req.json();
    try:
        # Use the first result
        result = res['results'][0];# Results obtained from Google service are stored in result variable
    #    print(result);
        geodata = dict(); # A variable is created to store attributes of the place found
        geodata['lat'] = result['geometry']['location']['lat'];  # The latitude attribute
        geodata['lng'] = result['geometry']['location']['lng'];  # The longitute attribute
        geodata['address'] = result['formatted_address']+' ('+search_term +')'; # The address attribute
        if pubcity == True: 
            geodata['pubcity'] = True;# If true then it is searching for publication city
        else:
            geodata['pubcity'] = False;
        geocodes.append(geodata);# All placess that were searched and found are stored in an array to be used later to put pins on the map
        print('{address}. (lat, lng) = ({lat}, {lng})'.format(**geodata));# Printing results
    except: 
           print('Search error for: '+search_term+' ',pubcity, sys.exc_info()[0]);# If any error ocurred it is printed out
    

@app.route('/')
def main():
    with io.open ('Boix_APSR_2010.txt',encoding='utf-8') as in_file: # opening text file
        emptyLine = 0;
        refLineRead = 0;
        surname = '';
        initials = '';
        for line in in_file: # loops until it reaches References section header
            if line.strip() == 'REFERENCES':  # If the current line is the references section header
                break # break the loop
        # start a new loop and read text until the end of the file
        for line in in_file:  # This keeps reading the file
#            print("Checking!!")
            line_cache.append(line);
            if line.strip() == 'End': # If end of the file, break
                break
            elif line in ['\n', '\r\n'] and  emptyLine < 2 :
                emptyLine= emptyLine+1;      
                if len(line_cache) > 4: # The lines are temporarilly stored in line_cache array
                #Search for a publication city if we have reached the first blank line and we have read atleast 4 lines from references section
                    publication_city = '';
                    if "." not in line_cache[len(line_cache) - 3] and "," not in line_cache[len(line_cache) - 3]:
                        # If one but last line has no . or , in the citation block, it means the last two lines of the block form the publication city/place name
                        publication_city= "%s %s"% (line_cache[len(line_cache) - 3].rstrip(),line_cache[len(line_cache) - 2].rstrip());
#                        print('One but last line has no . or ,');
                        print(surname);
                        print (publication_city);
                        if bool(re.search(r'\d', publication_city)):
                                print('Page numbers not address');
                        else:
                            search(publication_city, True);
                    elif "," in line_cache[len(line_cache) - 3] and not bool(re.search(r'\d', line_cache[len(line_cache) - 2])):                        
                        publication_city = line_cache[len(line_cache) - 2];
#                        print('One but last line has a , last line has no digits');
                        print(surname);
                        print (publication_city);
                        if bool(re.search(r'\d', publication_city)): 
                        # If the name has a digit, it means its a page number not a place name, so we do not search for it
                                    print('Page numbers not address');
                        else:
                            search(publication_city, True) 
                        # If it does not have a digit, we assume it is a place then we search for it from the Google serice
                    elif(bool(re.search(r'\d', line_cache[len(line_cache) - 2]))):
                        # If One but last line has a , last line has no digits, the last line in the citation block is a place so we search for it                        
                        publication_city = line_cache[len(line_cache) - 4];
#                        print('Last line has digits');
                        #print(surname);
                        print (publication_city);
                        if bool(re.search(r'\d', publication_city)):
                                    print('Page numbers not address');
                        else:
                            search(publication_city, True)
                    else:
                        publication_city = line_cache[len(line_cache) - 2];
                        # If none of the above, we take the list line as a place
#                        print('Something else');
                        print(surname);
                        print (publication_city);
#                    search(line_cache[len(line_cache) - 2], True);                        
            elif emptyLine == 2 and refLineRead ==0:
                # If we have read two blank lines already, it means the next line is author's surname for the next citation block            
                refLineRead = refLineRead+1;
                surname = line.replace('\n', ' ').replace('\r\n', ' ');# We store this next line in surname variable
            elif emptyLine == 2 and refLineRead ==1: 
                initials = line.replace('\n', ' ').replace('\r\n', ' ');# We store the initials in a variable                                  
                emptyLine =0;   
                refLineRead = 2;
            else:         # Re-initialise variables to default values        
                refLineRead = 0;
                emptyLine =0;  
                initials = '';
                surname = '';
            if initials not in ['\n', '\r\n', '']:
                try:
                    # Concatinate the surname and initials and search for the author using scholarly
                    author = next(scholarly.search_author(surname + ' ' + initials));                
                    print("\n======================= "+surname + " "+ initials+"===========================\n");                
#                    print(author);
#                    if bool(re.search(r'\d', publication_city)):
#                        print('Page numbers not address');
#                    else:
#                        search(publication_city,True); 
                    search(author.affiliation,False);# Get affiliation form scholarly results and search for it on Google service
                except: 
                    print('With open error: ',sys.exc_info()[0]);
#    browseLocal()
    locations = json.dumps([dict(loc=loca) for loca in geocodes]); 
    # All obtained locations are stored in a variable to be parsed to the browser for pinning
#    print(len(locations));
    print(locations);
    return render_template('affiliations.html', locations=locations)
    # Render the html page, affilliations.html which has JavaScript code and HTML to display the map and pins
