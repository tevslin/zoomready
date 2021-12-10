# -*- coding: utf-8 -*-
"""
Created on Sat Nov 13 09:49:24 2021

@author: tevsl
"""
version="0.0.5"

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import numpy as np
import time
import operator
import psutil
import warnings
warnings.filterwarnings("ignore")
import ping3
ping3.EXCEPTIONS = True
from cloudflarepycli import cloudflareclass

######## Note ping3 does not work in user mode in rasperian
    
class statusblock:  #keeps track of a performance dimension
    lastvalue=-1 #don't want match   
    lasttime=-1
    lastlevel=2 #assume good to start
    total=0
    count=0
    maxi=0
    mini=0
    q=[]
    #stype=np.dtype([('time',np.float),('level',np.int16)])  
    def __init__(self,theop,duration=0,levels=()):
        self.theop=theop
        self.levels=levels
        self.duration=duration
       
    def updateavg(self,value):
        now=time.time()
        nochange=value==self.lastvalue
        self.lastvalue=value
        self.lasttime=now
        self.total+=value
        self.count+=1
        self.maxi=max(self.maxi,value)
        self.mini=min(self.mini,value)
        if self.duration>0: #if we're doing an interval
            if nochange:    #if there hasn't been a change
                self.q.pop(-1) #get rid of redundant entry
            self.q.append((value,now))                          
            while self.q[0][1]-now>self.duration:   #pop old entries
                self.q.pop(0)
        if not nochange: 
            updatestatus()
        return (self.total/self.count)
    def getlevel(self,value): #get the level for a value
        if self.lasttime<0: #if hasn't happened yet
            return(self.lastlevel) #give it a pass
            
        for i,lim in enumerate(self.levels):
            if self.theop(value,lim):            
                return len(self.levels)-i
        return(0)   #lowest level if not found
            
      
        

class mainwindow:
    def __init__(self,callafter,aftertime,title='Zoomready'):
       
        self.root = tk.Tk()
        self.root.title(title+' '+version)
        self.frm = ttk.Frame(self.root, padding=10)
        self.canvas=tk.Canvas(self.root)
        self.row=-1 #current row
        self.column=0 #current column
        self.callafter=callafter
        self.aftertime=aftertime
        self.doingafter=None
        self.dict={}
        
    def addpair(self,label,vname=None,vinit='N/A',newrow=True):
        
        if newrow:
            self.row+=1
            self.column=0      
        ttk.Label (self.frm,text=label).grid(column=self.column,row=self.row,sticky='e')
        if vname is None: #if just another constant
            ttk.Label (self.frm,text=vinit).grid(column=self.column+1,row=self.row)
        else:
            strvar=tk.StringVar(self.root,vinit,name=vname)
            self.dict[vname]=strvar
            ttk.Label(self.frm,textvariable=strvar).grid(column=self.column+1,row=self.row)
        self.column+=2
        
    def addbutton(self,vinit,command,vname=None,newrow=True,column=None):      
        
        if newrow:
            self.row+=1
            self.column=0
        if not column is None: #if clomn specified
            self.column=column
        if vname is None: #if not variable text
            ttk.Button(self.frm,text=vinit,command=command).grid(column=self.column,row=self.row)
        else:
            strvar=tk.StringVar(self.root,vinit)
            self.dict[vname]=strvar
            ttk.Button(self.frm,textvariable=strvar,command=command).grid(column=self.column,row=self.row)
        self.column+=1
        
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
        
    def setvar(self,name,value):
        self.dict[name].set(value)


def circlist(thelist,theitem,maxlength):
    #adds theitem to the bottom of thelist and pops the top if maxlength exceeded
    thelist.append(theitem)
    if len(thelist)> maxlength:
        thelist.pop(0)

def getduration(oldtime):
    from datetime import timedelta  
    elapsed=timedelta(seconds=round(time.time()-oldtime))
    return str(elapsed)
        
def goodresult(curtask,index,ms):
    curtask["lastgood"]=time.time()
    curtask['conseq']+=1
    curtask['results'].append({"time":curtask['lastgood'],"index":index,"ms":ms}) #put it on the list
    circlist(curtask["results"],{"time":curtask['lastgood'],"index":index,"ms":ms},curtask['resultlim'])

def updatestatus(): #updates color bar and message
    colorset=('red','yellow','green')
    textset=('not zoomready','iffy','zoomready')
    if failstart>0: #if in failure
        color="red"
        thetext='no connection'
        minstatus=0
    else:
        minstatus=np.min([block.getlevel(block.lastvalue) for block in statusgroup ])
        color=colorset[minstatus]
        thetext=textset[minstatus]
        if possfailstart>0: #if in a glitch
            thetext+='-glitch' #should do something with color

            
    curstat.configure(text=thetext,background=color)

    avgstatus.updateavg(minstatus)
    minstatus=int(np.min([item[0] for item in avgstatus.q]))
    hourstat.configure(text=textset[minstatus],background=colorset[minstatus])
    
    
    
    
    
    
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
            mw.setvar("duration",getduration(failstart))
            mw.setvar("avgduration","{:5.2f}".format(avgduration.updateavg(time.time()-failstart)))
            failstart=0 #we're not failing any more
            
            lastfailend=time.time()
            
        if lastfailend>0:
            x=getduration(lastfailend)
            mw.setvar("lastfail",x)        

        if ms>0:   #if could find time  
           # ms=int(thetime)
            goodresult(curtask,index,ms)
            if len(curtask['results'])>=pingmin: #if have enough samples
                relresults=curtask["results"][-pingmin:]
                x=np.mean([res['ms'] for res in relresults])
                mw.setvar('latency',"{:4.1f}".format(x))
                mw.setvar('avglatency',"{:5.2f}".format(avglatency.updateavg(x)))
                
                
            # now work on jitter
               
                circlist(pingqs[index],ms,jittermin+1) #put the time at the bottom of the q
                if len(pingqs[index])>1: # if there's anything else on the list
                    pingqs[index][-2]=abs(pingqs[index][-2]-pingqs[index][-1]) #turn it into jitter
                    jit=np.mean([np.median(q) for q in pingqs[:-1] if len(q)>=5])
                    if not np.isnan(jit): #if enough to calculate
                        mw.setvar("jitter","{:4.1f}".format(jit))
                        mw.setvar("avgjitter","{:5.2f}".format(avgjitter.updateavg(jit)))
                    
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
                
                mw.setvar("lastfail",'now')
                failcount+=1
                mw.setvar("failcount",failcount)
            else:
                mw.setvar("duration",getduration(failstart))
        
    return(True) #always advance index
                
        
def dospeed(curtask,index):
    #performs speedtests
    if curtask['direction']=='up':
        results=cf.upload(curtask['script'][index],1)
        if results is None:  #allowing for bug in cloudflarecli
            results=()
    else:   #for download
        fulltimes,servertimes,requesttimes=cf.download(curtask['script'][index],1)
        results=fulltimes=np.subtract(fulltimes,requesttimes)
    if len(results)==0: #if it failed
        return(False)
    curtask['speeds'][index]=curtask['script'][index]*8/results[0] #update the results array
    if curtask['initializing']: #if still in itialization
        if index==len(curtask['speeds'])-1:  #if just filled last bucket
            curtask['initializing']=False #turn off iniialization
    if not curtask['initializing']: #if not in itialization
        speed=round(np.percentile(curtask['speeds'],thepercentile)/1e6,2)
        mw.setvar('speed'+curtask['direction'],str(speed))
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
    blob=[key for key in blob.keys() if blob[key].isup ] #look for adapters which are up
    #code below is windows specific
    if 'Ethernet' in blob:  #favor ethernet if there. could etst furthr by getting byte counts and see if they change
        ctype='Ethernet'
    elif 'Wi-Fi' in blob:
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


killsw=False
pausesw=False
failstart= 0 #any nonzero value means failure underway. blocks execution of nonping tests
possfailstart=0 #time of last test if it failed
failcount=0
lastfailend=0
hourstat=0
avgduration=statusblock(theop=operator.lt)
avglatency=statusblock(theop=operator.lt,levels=(75,100))
avgjitter=statusblock(theop=operator.lt,levels=(15,25))
avgdown=statusblock(theop=operator.gt,levels=(5,2))
avgup=statusblock(theop=operator.gt,levels=(3,1))
statusgroup=(avglatency,avgjitter,avgdown,avgup)

avgstatus=statusblock(theop=operator.le,levels=(5,3,2,1),duration=3600)
cf =cloudflareclass.cloudflare(printit=False)

pingtasks=[('8.8.8.8',1),('1.1.1.1',1),('208.67.222.222',1)] #locations to ping and weighting
pingqs=[[] for i in range(len(pingtasks))]

pingdict={"task":do_ping,"interval":1,"timeout":.200,"results":[],"conseq":0,"resultlim":12,
          "lastgood":0,"initializing":True}  # will come from preferences
pingdict["script"]=maketaskarray(pingtasks) #add scripts and output array
featuredict={'ping':pingdict,"speeddown":makespeeddict(cf.downloadtests,'down'),'speedup':makespeeddict(cf.uploadtests,'up')}    

thequeue=[] #revolving q of tasks to schedule
for feature, dictionary in featuredict.items():    #create a queue and thread for each feature
    thequeue.append({"name":feature,"interval":dictionary["interval"],"last":0,"index":0})


        
    
buttonignore=True #because buttons call their code during setup     
mw=mainwindow(checkstatus,200)   #create the window


mw.addpair('started ',vinit=time.asctime())
mw.addpair('ISP:',"isp")
mw.addpair('Connection:','conn',newrow=False)
mw.addpair("IP address","IP")
mw.addpair('time since failure:','lastfail')
mw.addpair('failure count:','failcount',vinit=str(0),newrow=False)
mw.addpair('last failure duration:','duration')
mw.addpair('average:','avgduration',newrow=False)
mw.addpair ('current latency in ms:',"latency")
mw.addpair ("average:","avglatency",newrow=False)
mw.addpair ('current jitter in ms:',"jitter")
mw.addpair ("average:","avgjitter",newrow=False)
mw.addpair("speed down in Mbps:","speeddown")
mw.addpair ("speed up:","speedup",newrow=False)
mw.addbutton("Pause",pausetoggle,vname="pausebutton")
mw.addbutton("Quit",killall,newrow=False,column=3)
ttk.Label (mw.canvas,text='current status').grid(column=0)
ttk.Label(mw.canvas,text='last hour minimum status').grid(row=0,column=3,sticky="e")
curstat=ttk.Label(mw.canvas,text='N/A')
curstat.grid(row=1,column=0)
hourstat=ttk.Label(mw.canvas,text='N/A')
hourstat.grid(row=1,column=3)


mw.canvas.grid(rowspan=4)
mw.frm.grid()

buttonignore=False #now buttons are good to go
mw.doafter(aftertime=0,callafter=getisp) #get isp infor before real start to test internet connection
mw.mainloop()

print('goodbye')