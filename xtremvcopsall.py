#!/usr/bin/python

import paramiko
import requests
import time
import sys
import logging
import pprint

logFormatter = logging.Formatter("%(asctime)s [%(module)s:%(funcName)s] [%(levelname)-5.5s]  %(message)s")


rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

fileHandler = logging.FileHandler("xtremvcops.log")
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(logging.DEBUG)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
consoleHandler.setLevel(logging.INFO)
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
    rootLogger.debug("returned from clicommand stdout %s",output)
    rootLogger.debug("returned from clicommand stderr %s",stderr.readlines())
    ssh.close()
    return output
    
def cookSystemResults(output):
    rootLogger.debug("processing command as system result %s",output)
    alldata = []
    data = {'arrayname': "", 'index': "", 'WriteBW': "", 'WriteIO': "", 'ReadBW': "", 'ReadIO': "", 'BW': "", 'IOPs': "", 'TotalWriteIO': "", 'TotalReadIO': ""}
    for line in output[1:]:
        data['arrayname'],data['index'],data['WriteBW'],data['WriteIO'],data['ReadBW'],data['ReadIO'],data['BW'],data['IOPs'],data['TotalWriteIO'],data['TotalReadIO'] = line.split()
        rootLogger.debug("appending to alldata for this run %s",data)
        alldata.append(data)
    return alldata[0]
    
def getSystemName():
    raw = runPerfCommand("show-systems-info")
    systemname = raw[-1].split()[0]
    rootLogger.info("Returning system name as: %s",systemname)
    return systemname

def collectPerf():
    systemName = getSystemName()
    systemFirstLine = buildSystemFirstLine(systemName)
    systemMetricLines = buildSystemMetricLines(cookSystemResults(runPerfCommand("show-systems-performance")))
    postMetrics(systemFirstLine,systemMetricLines)
    buildVolumesMetricLines(systemName)

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
    for metricName in cookedperfdata:
        if (metricName != 'arrayname') & (metricName != 'index'):
            value = str(cookedperfdata[metricName])
            metricLine = ",".join([metricName,alarmLevel,alarmMessage,date,value])
            allLines.append(metricLine)
    return allLines
    
def buildVolumeFirstLine(systemName,volumeName):
    resourceName = "-".join(["XtremIO",systemName,volumeName])
    adapterKindKey = "XtremIO-Adapter"
    resourceKindKey = "XtremIO-Volume"
    identifiers = ""
    resourceDescription = "-".join(["XtremIO","Array",systemName,volumeName])
    monitoringInterval = '1'
    storeOnly = 'false'
    sourceAdapter = 'XtremIO-Alpha-Demo-Adapter'
    disableResourceCreation = 'false'
    firstLine = ",".join([resourceName,adapterKindKey,resourceKindKey,identifiers,resourceDescription,monitoringInterval,storeOnly,sourceAdapter,disableResourceCreation])
    return firstLine

def buildVolumesMetricLines(systemName):
    alarmLevel = "0"
    alarmMessage = "NA"
    date = str(int(time.time()*1000))
    rawVolumeMetrics = runPerfCommand("show-volumes-performance")
    rootLogger.debug("processing command as volumes result %s",rawVolumeMetrics)
    for volume in rawVolumeMetrics[1:]:
        data = {'volumeName': "", 'index': "", 'WriteBW': "", 'WriteIO': "", 'ReadBW': "", 'ReadIO': "", 'BW': "", 'IOPs': "", 'TotalWriteIO': "", 'TotalReadIO': ""}
        data['volumeName'],data['index'],data['WriteBW'],data['WriteIO'],data['ReadBW'],data['ReadIO'],data['BW'],data['IOPs'],data['TotalWriteIO'],data['TotalReadIO'] = volume.strip().split()
        firstLine = buildVolumeFirstLine(systemName,data['volumeName'])
        volumeMetrics = []
        for metricName in data:
            if (metricName != 'volumeName') & (metricName != 'index'):
                value = str(data[metricName])
                metricLine = ",".join([metricName,alarmLevel,alarmMessage,date,value])
                volumeMetrics.append(metricLine)
        postMetrics(firstLine,volumeMetrics)
        
        
    
def postMetrics(firstLine,metricLines):
    rootLogger.info("entering vcops post for resource name: %s",firstLine.split(',')[0])
    allMetrics = "\n".join(metricLines)
    postData = "\n".join([firstLine,allMetrics])
    
    rootLogger.debug("final post data \n\n--------------\n%s\n--------------\n",postData)
    r = requests.post(vcopsurl, postData, auth=(vcopsuser, vcopspass), verify=False)
    r.raise_for_status()
    rootLogger.info("post result %s",r.status_code)



if __name__ == '__main__':
    while True:
        collectPerf()
        rootLogger.info("sleeping 60s before next run")
        time.sleep(60)

        
    