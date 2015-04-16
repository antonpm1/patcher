#!/usr/bin/python
from datetime import datetime
import xmlrpclib
import sys
import time
import getpass

SATELLITE_URL = "http://ansible.antonpm.co.uk/rpc/api"
SATELLITE_LOGIN = "api-user"
SATELLITE_PASSWORD = getpass.getpass()

system=sys.argv[1]

now=datetime.today()
dateString='%s-%s-%s' % (now.year, now.month, now.day)
earliest_occurrence=xmlrpclib.DateTime(now)

client = xmlrpclib.Server(SATELLITE_URL, verbose=0)
key = client.auth.login(SATELLITE_LOGIN, SATELLITE_PASSWORD)

class System:

    def __init__(self, system):
        self.system=system

    def systemID(self):
        sysCall=client.system.searchByName(key, self.system)
        for sysID in sysCall:
            return sysID.get('id')

    def kernelVer(self):
        kernVer=client.system.getRunningKernel(key, self.systemID())
        return kernVer

    def sysOnline(self):
	status=client.system.getDetails(key, self.systemID())
	return status.get('osa_status')

sysObj=System(system)

def createProfile(system):
    packageProfile=client.system.createPackageProfile(key, sysObj.systemID(), system + "-" + dateString, "Package profile for " + system + "on " + dateString)

def addNote(system):
    note=client.system.addNote(key, sysObj.systemID(), "Patching", "Server patched on "+dateString)
    
def sysUpgrade(system):
    packArray=[]
    reboot=0
    packages=client.system.listLatestUpgradablePackages(key, sysObj.systemID())
    for package in packages:
	packArray.append(package.get('to_package_id'))

    if "kernel" in packages:
	reboot=1
    else:
	reboot=0
    createProfile(system)
    install=client.system.schedulePackageInstall(key, sysObj.systemID(), packArray, earliest_occurrence)
    print "Scheduled upgrade of "+system
    return install, reboot

def taskStatus(system, taskID, type):
    events=client.system.listSystemEvents(key, system)
    for event in events:
        if taskID == event.get("id"):
            if event.get(type) >= 1:
                return 1
            else:
                return 0

def installAndTrack(system):
    sysID=sysObj.systemID()

    if sysObj.sysOnline() != "online":
	print "System is not online, exiting upgrade process"
	exit( 1 )

    taskID, reboot=sysUpgrade(system)
    success=0
 
    count=0
    while count < 13:
        if taskStatus(sysID, taskID, "pickup_time") == 1:
	    print "Task picked up successfully"	
	    break
        elif count == 12:
	    print "Task not picked up after 2 minutes"
	    exit ( 1 )
        time.sleep( 10 )
	count+=1

    while True:
	if taskStatus(sysID, taskID, "failed_count") == 1:
	    print "Upgrade task has failed!" 
            success=0
	    break
	elif taskStatus(sysID, taskID, "successful_count") == 1:
	    print "Upgrade task has completed!"
            success=1
	    break    
	else:
	    print "Sleeping 30 seconds to allow upgrade to continue"
	    time.sleep( 30 )

    if (success == 1) and (reboot == 1):
	print "Reboot required"
    else:
	print "No reboot required"

installAndTrack(system)
