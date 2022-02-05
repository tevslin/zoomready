# -*- coding: utf-8 -*-
"""
Created on Tue Jan  4 18:18:12 2022

@author: tevsl
"""
def parseversion(vstring):    
    parts=vstring.split('.')
    nums=[0,0,0]
    for  i,part in enumerate(parts):
        if part.isdecimal():
            nums[i]=int(part)
        else:
            raise Exception('malformed version')
    return nums
    
    
        
def getlatestversioninfo(url,curversion,timeout=(3.03,30)):
    #retrieves text containing a version number in the form xx.yy.zz from a URL and parses
    #returns text in lines
    # line 0 release in canonical form
    #line 1 text about release
    #line 2 button tezt
    #line 3 url of release notes
    
    import requests
    
    r=requests.get(url,timeout=timeout)
    lines=r.text.splitlines()
    if len(lines)<4: # if malformed text
        raise Exception ('too few input lines')
    newversion=parseversion(lines[0])
    oldversion=parseversion(curversion)
    new=False
    for i,vers in enumerate(newversion):
        if vers<oldversion[i]: #if newer than production
            break #must be prerelease
        if vers>oldversion[i]:
            new=True
            break
    return (new,lines)

   

   
    
