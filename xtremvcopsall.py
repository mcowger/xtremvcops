#!/usr/bin/python

import paramiko
import requests
import time
import sys
import logging

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
#logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  {}")

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

fileHandler = logging.FileHandler("xtremvcops.log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
        

# SC
# sshuser = 'root'
# sshpass = '123456'
# xmsip = '10.6.121.190'
# xmcliuser = 'tech'
# xmclipass = '123456'


# BRS 
sshuser = 'root'
sshpass = '123456'
xmsip = '10.241.105.151'
xmcliuser = 'mcowger'
xmclipass = 'P@ssword1!'


vcopsurl = "https://10.5.132.62/HttpPostAdapter/OpenAPIServlet"
vcopsuser = 'admin'
vcopspass = 'P@ssword1!'



def runPerfCommand(xmclicommand):
    rootLogger.info("entered clicommand for command %s", xmclicommand)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(xmsip,username=sshuser,password=sshpass)
    command = " ".join(["xmcli","-u",xmcliuser,"-p",xmclipass,"-c",xmclicommand])
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.readlines()
    rootLogger.info("returned from clicommand stdout %s",output)
    rootLogger.debug("returned from clicommand stderr %s",stderr.readlines())
    return output
    
def cookSystemResults(output):
    rootLogger.info("processing command as system result %s",output)
    alldata = []
    data = {'arrayname': "", 'index': "", 'WriteBW': "", 'WriteIO': "", 'ReadBW': "", 'ReadIO': "", 'BW': "", 'IOPs': "", 'TotalWriteIO': "", 'TotalReadIO': ""}
    for line in output[1:]:
        data['arrayname'],data['index'],data['WriteBW'],data['WriteIO'],data['ReadBW'],data['ReadIO'],data['BW'],data['IOPs'],data['TotalWriteIO'],data['TotalReadIO'] = line.split()
        rootLogger.info("appending to alldata for this run %s",data)
        alldata.append(data)
    return alldata[0]
    
def getSystemName():
    raw = runPerfCommand("show-systems-info")
    systemname = raw[-1].split()[0]
    rootLogger.info("Returning system name as: %s",systemname)
    return systemname

def collectPerf():
    systemFirstLine = buildSystemFirstLine(getSystemName())
    systemMetricLines = buildSystemMetricLines(cookSystemResults(runPerfCommand("show-systems-performance")))
    postMetrics(systemFirstLine,systemMetricLines)

def buildSystemFirstLine(systemName):
    resourceName = "-".join(["XtremIO",systemName])
    adapterKindKey = "XtremIO-Adapter"
    resourceKindKey = "XtremIO-Array"
    identifiers = ""
    resourceDescription = "-".join(["XtremIO","Array",systemName])
    monitoringInterval = '1'
    storeOnly = 'false'
    sourceAdapter = 'XtremIO-Alpha-Demo-Adapter'
    disableResourceCreation = 'false'
    firstLine = ",".join([resourceName,adapterKindKey,resourceKindKey,identifiers,resourceDescription,monitoringInterval,storeOnly,sourceAdapter,disableResourceCreation])
    return firstLine
    
def buildSystemMetricLines(cookedperfdata):
    allLines = []
    alarmLevel = "0"
    alarmMessage = "NA"
    date = str(int(time.time()*1000))
    print cookedperfdata
    for metricName in cookedperfdata:
        if (metricName != 'arrayname') & (metricName != 'index'):
            value = str(cookedperfdata[metricName])
            metricLine = ",".join([metricName,alarmLevel,alarmMessage,date,value])
            allLines.append(metricLine)
    return allLines
    
def postMetrics(firstLine,metricLines):
    rootLogger.info("entering vcops post for firstline %s",firstLine)
    allMetrics = "\n".join(metricLines)
    postData = "\n".join([firstLine,allMetrics])
    
    rootLogger.info("final post data \n\n--------------%s\n--------------\n",postData)
    r = requests.post(vcopsurl, postData, auth=(vcopsuser, vcopspass), verify=False)
    r.raise_for_status()
    rootLogger.info("post result %s",r.status_code)


collectPerf()


        

        
    