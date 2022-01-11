# -*- coding: utf-8 -*-
"""
Created on Sat Nov 13 09:49:24 2021

@author: tevsl
"""
version="1.0.2"

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import numpy as np
import time
import operator
import psutil
from datetime import timedelta
import webbrowser
import sys
import os
import warnings
warnings.filterwarnings("ignore")
import ping3
ping3.EXCEPTIONS = True
import versionutils
from cloudflarepycli import cloudflareclass

######## Note ping3 does not work in user mode in raspberian
    
class statusblock:  #keeps track of a performance dimension
    lastvalue=-1 #don't want match   
    lasttime=-1
    
    total=0
    count=0


    duration=3600 #work in hours
    #stype=np.dtype([('time',np.float),('level',np.int16)])  
    def __init__(self,theop,duration=3600,levels=(),widget=None,exit=None):
        self.theop=theop
        self.levels=levels
        self.duration=duration
        self.widget=widget
        self.exit=exit
        self.q=[]
        self.tq=[] #can't slice q the way I want
        self.lastlevel=len(colorset)-1 #assume good to start
       
    def updateentries(self,value): #renamed 12/18
    #updates entry and average as well as any visible fields in window
        if value>-1: #minus = no update += used to update display
            now=time.time()
            self.lastvalue=value
            self.lasttime=now
            self.total+=value
            if self.count==0:
                self.maxi=value
                self.mini=value            
            self.count+=1
            self.maxi=max(self.maxi,value)
            self.mini=min(self.mini,value)
            if self.duration>0: #if we're doing an interval 
                self.q.append(value)
                self.tq.append(now)                          
    
        if self.theop == operator.le or self.theop==operator.lt:
            if len(self.q)>0:
                hnadir=np.max(self.q)
            else:
                hnadir=0
            nadir=self.maxi
        else:
            hnadir=np.min(self.q)
            nadir=self.mini
            
        values=[value,0 if len(self.q)==0 else np.mean(self.q),hnadir,self.total/self.count,nadir]
        for i,suffix in enumerate(suffi):
            if values[i]>-1:    #if value really there
                if suffix in ["cur","lhnadir","nadir"]: #if current or nadir
                    lastlevel=self.getlevel(values[i])
                    background=colorset[lastlevel]
                    if suffix=='cur':   #if current last level
                        self.lastlevel=lastlevel #remember it
                else: #if average
                    background=None #it doesn't have a color
                if not self.widget is None:  #if it has a widget
                    if self.exit is None: #if no exit
                        mw.setvar(self.widget+suffix,"{:4.1f}".format(values[i]),background=background)
                    else:
                        thevalue,background=self.exit(values[i],suffix)
                        mw.setvar(self.widget+suffix,thevalue,background=background)
        return (self.total/self.count)
    
    def getlevel(self,value): #get the level for a value
        if self.lasttime<0: #if hasn't happened yet
            return(self.lastlevel) #give it a pass
            
        for i,lim in enumerate(self.levels):
            if self.theop(value,lim):            
                return len(self.levels)-i
        return(0)   #lowest level if not found
            
      
        

class mainwindow:
    def __init__(self,callafter,aftertime,title='zoomready'):
       
        self.root = tk.Tk()
        self.root.title(title+' '+version)
        try:
            self.root.iconbitmap('theicon.ico')
        except Exception:
            self.root.iconbitmap(os.path.join(sys._MEIPASS,'theicon.ico'))
        self.frm = ttk.Frame(self.root, padding=10)
        self.frm1=ttk.Frame(self.root,padding=10)    
        self.callafter=callafter
        self.aftertime=aftertime
        self.doingafter=None
        self.dict={}
        
    def getnextpos(self,base,newrow): #gets the next row and column position in frame
        if base is None: #if in main window
            thebase=self.frm
        else:
            thebase=base
        try:
            info=thebase.winfo_children()[-1].grid_info()
        except IndexError:  #frame has no widgets
            return(thebase,0,0)
        row=info['row']+(info['rowspan'] if newrow else 0)
        column=0 if newrow else (info['column']+info['columnspan'])
        return thebase,row,column
        
    def addpair(self,label,vname=None,vinit='N/A',newrow=True,base=None):

        thebase,row,column=self.getnextpos(base,newrow)

        ttk.Label (thebase,text=label).grid(row=row,column=column,sticky='e')
        if vname is None: #if just another constant
            ttk.Label (thebase,text=vinit).grid(row=row,column=column+1,sticky='w')
        else:            
            self.dict[vname]=ttk.Label(thebase,text=vinit)
            self.dict[vname].grid(row=row,column=column+1,sticky='w')

        #self.column+=2
        
    def addrow(self,label,vinit='N/A',base=None):
        thebase,row,column=self.getnextpos(base,True)
        ttk.Label (thebase,text=label).grid(column=0,sticky='e')
        skip=0 #for column skipping
        for i,suffix in enumerate(suffi):
            self.dict[label+suffix]=ttk.Label(thebase,text=vinit)
            self.dict[label+suffix].grid(column=1+i+skip,row=row)
            if 2+i+skip in sepcols: #if next column should be skipped
                skip+=1 #set it up
            
                
        
    def addbutton(self,vinit,command,vname=None,newrow=True,col=None,base=None):      
        thebase,row,column=self.getnextpos(base,newrow)

        if not col is None: #if column specified
            column=col
        if vname is None: #if not variable text
            ttk.Button(thebase,text=vinit,command=command).grid(column=column,row=row)
        else:
            self.dict[vname]=ttk.Button(thebase,text=vinit,command=command)
            self.dict[vname].grid(column=column,row=row)
        #self.column+=1
        
    def doafter(self,aftertime=None,callafter=None):
        if aftertime is None:
            aftertime=self.aftertime
        if callafter is None:
            callafter=self.callafter
        self.doingafter=self.root.after(aftertime,callafter)
        
    def mainloop(self):
        self.root.mainloop()
        
    def cancel(self):
        self.root.after_cancel(self.doingafter)
        
    def setvar(self,name,value,background=None):
        self.dict[name].config(text=value,background=background) #changed 12/18 to do bg as well as text


def circlist(thelist,theitem,maxlength):
    #adds theitem to the bottom of thelist and pops the top if maxlength exceeded
    thelist.append(theitem)
    if len(thelist)> maxlength:
        thelist.pop(0)

def getduration(oldtime):
    
    elapsed=timedelta(seconds=round(time.time()-oldtime))
    return str(elapsed)
        
def goodresult(curtask,index,ms):
    curtask["lastgood"]=time.time()
    curtask['conseq']+=1
    curtask['results'].append({"time":curtask['lastgood'],"index":index,"ms":ms}) #put it on the list
    circlist(curtask["results"],{"time":curtask['lastgood'],"index":index,"ms":ms},curtask['resultlim'])

    
def statusexit(value,suffix):
        
    if suffix in ["cur","lhnadir","nadir"]: #if current or nadir
        index=int(np.floor(value))
        color=colorset[index]
        if color=='':
            color='green' #status is special
        return(textset[index],color)
    
    return("{:2.2f}".format(value),None)       
    
def updatestatus(): #updates color bar and message
    expgroup=statusgroup+(avgstatus,)
    for entry in expgroup: #timeout the qs
        pop=False
        while len(entry.q)>0 and entry.tq[0]+3600<time.time():
            entry.q.pop(0)
            entry.tq.pop(0)
            pop=True
        if pop: #if anything changed
            entry.updateentries(-1) #update display
    if failstart>0: #if in an outage
        minstatus=0 #red alarm
    else:
        minstatus=np.min([block.lastlevel for block in statusgroup ]) #changed 12/18
    avgstatus.updateentries(minstatus)

    
def do_ping(curtask,index):
      
    pingmin=4
    jittermin=10
    pingfailmax=5 #seconds until failure declared
    
    global failstart #tracks ongoing failure
    global possfailstart
    global failcount
    global lastfailend
    
    ms=-1
    try:
        resp=ping3.ping(curtask['script'][index],unit='ms',timeout=curtask['timeout'])
        ms=round(resp)
        returncode=0
    except ping3.errors.HostUnknown:
        returncode=1
    except ping3.errors.Timeout:        
        returncode=2
    except ping3.errors.PingError:
        returncode=3
    except:
        returncode=99
    #glop=subprocess.run("ping "+curtask['script'][index]+' -n 1 -w '+str(curtask['timeout']),capture_output=True, shell=True)
    if returncode==0:  #if it succeeded
        possfailstart=0
        if failstart>0: #if we were in a failure
            
            failures.updateentries(time.time()-failstart) #this is the final duration
            
            failstart=0 #we're not failing any more
            failures.lastvalue=0
            failures.lastlevel=len(colorset) #clean up level
            mw.setvar('failure durationcur','N/A',background='')
            lastfailend=time.time()          
        if lastfailend>0:
            x=getduration(lastfailend)
            mw.setvar("lastfail",x,background='')        
            mw.setvar('lasthour',len(failures.q))
        if ms>0:   #if could find time  
           
            goodresult(curtask,index,ms)
            if len(curtask['results'])>=pingmin: #if have enough samples
                relresults=curtask["results"][-pingmin:]
                x=np.mean([res['ms'] for res in relresults])
                avglatency.updateentries(x) 
                
            # now work on jitter
               
                circlist(pingqs[index],ms,jittermin+1) #put the time at the bottom of the q
                if len(pingqs[index])>1: # if there's anything else on the list
                    pingqs[index][-2]=abs(pingqs[index][-2]-pingqs[index][-1]) #turn it into jitter
                    jit=np.mean([np.median(q) for q in pingqs[:-1] if len(q)>=jittermin])
                    if not np.isnan(jit): #if enough to calculate
                        avgjitter.updateentries(jit)

                    
    else:   #if ping failed
        print ('ping fail',index,time.time())
    # at some point must show failure cause somewhere. skipping for now
        if curtask['conseq']>0 or curtask['lastgood']==0 : #if last did not fail       
            curtask['conseq']=0 #break the string
            possfailstart=time.time() #remember possible failure start
        faillength=time.time()-possfailstart
        #print('fail length',faillength)
        if pingfailmax<faillength: #if we reached limit of our patience
            if not failstart>0: #if not already in outage
                print ('now in outage')
                failstart=possfailstart             
                mw.setvar("lastfail",'now',background='red')
                failcount+=1
                mw.setvar("totfailcount",failcount)
            mw.setvar("failure durationcur",getduration(failstart),background='red')
            avgstatus.updateentries(0) #report the failure
        
    return(True) #always advance index
                
        
def dospeed(curtask,index):
    #performs speedtests
    if curtask['direction']=='up':
        results=cf.upload(curtask['script'][index],1)
        if len(results)==0:  
            return(False)
    else:   #for download
        fulltimes,servertimes,requesttimes=cf.download(curtask['script'][index],1)
        if len(fulltimes)==0: #if it failed
            return(False)
        results=np.subtract(fulltimes,requesttimes)
    curtask['speeds'][index]=curtask['script'][index]*8/results[0] #update the results array

    if curtask['initializing']: #if still in itialization
        if index==len(curtask['speeds'])-1:  #if just filled last bucket
            curtask['initializing']=False #turn off iniialization
    if not curtask['initializing']: #if not in itialization
        speed=round(np.percentile(curtask['speeds'],thepercentile)/1e6,2)

        if curtask['direction']=='up': #12/18
            avgup.updateentries(speed)
        else:
            avgdown.updateentries(speed)

    return(True)
    

    


def maketaskarray(tasklist):  #formats script of tasks to run and results array for output
    script=[]
    for task in tasklist: #make the script
        for i in range(task[1]): #for weighting
            script.append(task[0])
    return script

def makespeeddict(functasks,direction):
    #makes dictionary defining a speed test function
    dict={}
    dict['script']=maketaskarray(functasks)
    dict['speeds']=np.zeros(len(dict['script']))
    dict['task']=dospeed
    dict['interval']=speedtestinterval*60/len(dict['script'])
    dict['results']=[]
    dict['resultlim']=12
    dict["conseq"]=0
    dict['lastgood']=0
    dict["direction"]=direction
    dict["initializing"]=True
    return dict
    


def checkstatus():
    if killsw:  #if we're done
        return #return without rescheduling
    if not pausesw: # if not paused
        for task in thequeue: #loop thru the queue
            curtask=featuredict[task["name"]] #get full feature record
            if possfailstart>0 or \
              (task["last"]+(1 if curtask['initializing'] else task['interval'])<=time.time()): #if due to run
                if (possfailstart==0) or (task['name']=='ping'): #only ping runs during failure - may use an attribute instead                  
                    if curtask["task"](curtask,task["index"]): #call the task and advance index if it wants
                        task["index"]=(task["index"]+1)%len(curtask["script"]) #update index
                    task["last"]=time.time() #remember when               
                    thequeue.append(thequeue.pop(0)) #move to back of queue
                    break
        updatestatus()
    mw.doafter() #set next iteration
    
#button processor
            
def killall(): #action for quit button
    global killsw
    
    killsw=True #in case lingering calls
    print("shutting down....")
    if mw.doingafter is not None:
        mw.cancel()
    mw.root.destroy()


def pausetoggle():  #action for pause button
    global pausesw
    
    if pausesw: #if already paused
        pausesw=False #resume
        mw.setvar("pausebutton","Pause")
    else: #if not paused
        pausesw=True
        mw.setvar("pausebutton","Resume")
        

        
def loadhelp(): #action for help button
    webbrowser.open('https://zoomready.s3.amazonaws.com/zoomreadycheatsheet.html')
def loadnewversion(): #action for info button
    webbrowser.open(vtext[3])

def getisp():   #gets data for isp and exits if no ip connection
    gotit=False
    while not gotit:
        try:
            colo,ip=cf.getcolo()
            gotit=True
        except:
            reply=messagebox.askretrycancel("Error","There doesn't seem to be an internet connection.")
            if not reply: #if user doesn't want to retry
                killall()
                return #just get out of dodge
    isp=cf.getisp(ip) #get the name of the isp
    mw.setvar('isp',isp)
    mw.setvar('IP',ip)
    blob=psutil.net_if_stats()
    blob=[key[0:3] for key in blob.keys() if blob[key].isup ] #look for adapters which are up
    #code below is windows specific
    if 'Eth' in blob or 'eth' in blob:  #favor ethernet if there. could test furthr by getting byte counts and see if they change
        ctype='Ethernet'
    elif 'Wi-' in blob or 'wla' in blob:
        ctype='WiFi'
    else:
        ctype='unknown'
    mw.setvar('conn',ctype)
    mw.doafter()

# initialization

try:
    import pyi_splash
    pyi_splash.update_text('Zoomready Loaded ...')
    pyi_splash.close()
except:
    pass

speedtestinterval=15  #should come from preferance. time in minutes for full set of type of speedtest
thepercentile=90
colorset=('red','orange','yellow','')
textset=('not connected','not zoomready','iffy','zoomready')
suffi=("cur","lhavg","lhnadir","avg","nadir")
sepcols=(2,5) #columns here the vertical seperator lines wil go


killsw=False
pausesw=False
failstart= 0 #any nonzero value means failure underway. blocks execution of nonping tests
possfailstart=0 #time of last test if it failed
failcount=0
lastfailend=0
hourstat=0
avgduration=statusblock(theop=operator.lt)
avglatency=statusblock(theop=operator.lt,levels=(75,100,1000),widget='latency')
avgjitter=statusblock(theop=operator.lt,levels=(15,25,1000),widget='jitter')
avgdown=statusblock(theop=operator.gt,levels=(5,2,0),widget='speed down')
avgup=statusblock(theop=operator.gt,levels=(3,1,0),widget='speed up')
failures=statusblock(theop=operator.le,levels=(0,1,1),widget='failure duration')
statusgroup=(avglatency,avgjitter,avgdown,avgup,failures)

avgstatus=statusblock(theop=operator.ge,levels=(2,1,0),exit=statusexit,widget='status')
failurecount=statusblock(theop=operator.le) #only used for tracking failure counts
cf =cloudflareclass.cloudflare(printit=False)

pingtasks=[('8.8.8.8',1),('1.1.1.1',1),('208.67.222.222',1)] #locations to ping and weighting
pingqs=[[] for i in range(len(pingtasks))]

pingdict={"task":do_ping,"interval":1,"timeout":.200,"results":[],"conseq":0,"resultlim":12,
          "lastgood":0,"initializing":True}  # will come from preferences
pingdict["script"]=maketaskarray(pingtasks) #add scripts and output array
uploadtests=((101000,8,'100kB'),(1001000, 6,'1MB'),(10001000, 4,'10MB'))
downloadtests=((101000, 10,'100kB'),(1001000, 8,'1MB'),(10001000, 6,'10MB'),(25001000, 4,'25MB'))


featuredict={'ping':pingdict,"speeddown":makespeeddict(cf.downloadtests,'down'),'speedup':makespeeddict(uploadtests,'up')}    

thequeue=[] #revolving q of tasks to schedule
for feature, dictionary in featuredict.items():    #create a queue and thread for each feature
    thequeue.append({"name":feature,"interval":dictionary["interval"],"last":0,"index":0})

# look for new version BEFORE setting up window
# just assume no new version if it fails for any reason
try:
    newversion, vtext =versionutils.getlatestversioninfo( \
        'https://zoomready.s3.amazonaws.com/zoombuddy_release.txt',version)
except:
    newversion=False
    
        
    
buttonignore=True #because buttons call their code during setup     
mw=mainwindow(checkstatus,200)   #create the window


mw.addpair('last hour failures:','lasthour',vinit=str(0),base=mw.frm1)
mw.addpair('total failures:','totfailcount',vinit=str(0),newrow=False,base=mw.frm1)
mw.addpair('time since failure:','lastfail',base=mw.frm1,newrow=False)
mw.addpair('connection:','conn',base=mw.frm1)
mw.addpair("IP address:","IP",newrow=False,base=mw.frm1)
mw.addpair('ISP:',"isp",base=mw.frm1,newrow=False)
base,row,column=mw.getnextpos(mw.frm,True)
toprow=row #remeber for tsretching vertical seperators
ttk.Label(base,text='Current').grid(row=row,column=1,columnspan=2)
ttk.Label(base,text='Last Hour').grid(row=row,column=3,columnspan=2)
ttk.Label(base,text='Since '+time.strftime('%m/%d %H:%M')).grid(row=row,column=6,columnspan=2)
row+=1
ttk.Label(mw.frm,text='average').grid(row=row,column=3)
ttk.Label(mw.frm,text='worst').grid(row=row,column=4)
ttk.Label(mw.frm,text='average').grid(row=row,column=6)
ttk.Label(mw.frm,text='worst').grid(row=row,column=7)
mw.addrow('status')
mw.addrow("latency")
mw.addrow('jitter')
mw.addrow("speed down")
mw.addrow("speed up")
mw.addrow('failure duration')
base,row,column=mw.getnextpos(mw.frm,True) #find out where we are now
for col in sepcols: #draw the seperato columns
    ttk.Separator(base, orient=tk.VERTICAL).grid(column=col, row=toprow, rowspan=row-toprow, sticky='ns')
if newversion: #if new vesion detected
    base,row,column=mw.getnextpos(mw.frm1,True) #find oout where are

    ttk.Label(base,text=vtext[1],background='yellow').grid(row=row,column=column,
        columnspan=4,sticky='e')
    ttk.Button(base,text=vtext[2],command=loadnewversion).grid( \
        row=row,column=4,columnspan=2)
    ttk.Label(base,text='').grid(row=row+1) #blank line
    
mw.addbutton('Help',loadhelp,base=mw.frm1)
mw.addbutton("Pause",pausetoggle,vname="pausebutton",newrow=False,col=4,base=mw.frm1)
mw.addbutton("Quit",killall,newrow=False,col=5,base=mw.frm1)


mw.frm.grid()
mw.frm1.grid(rowspan=6)

buttonignore=False #now buttons are good to go
mw.doafter(aftertime=0,callafter=getisp) #get isp info before real start to test internet connection
mw.mainloop()

print('goodbye')