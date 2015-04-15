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

def systemSearch(system):
    sysCall=client.system.searchByName(key, system)
    for sysID in sysCall:
	 return sysID.get('id')

def createProfile(system):
    sysID=systemSearch(system)
    packageProfile=client.system.createPackageProfile(key, sysID, system + "-" + dateString, "Package profile for " + system + "on " + dateString) 

def addNote(system):
    sysID=systemSearch(system)
    note=client.system.addNote(key, sysID, "Patching", "Server patched on "+dateString)
    
def sysUpgrade(system):
    packArray=[]
    reboot=0
    sysID=systemSearch(system)
    packages=client.system.listLatestUpgradablePackages(key, sysID)
    for package in packages:
	packArray.append(package.get('to_package_id'))

    if "kernel" in packages:
	reboot=1
    else:
	reboot=0

    createProfile(system)
    install=client.system.schedulePackageInstall(key, sysID, packArray, earliest_occurrence)
    print "Scheduled upgrade of "+system
    return install, reboot

def taskStatus(system, taskID, type):
    events=client.system.listSystemEvents(key, system)
    for event in events:
        if taskID == event.get("id"):
            if type in event:
                return 1
            else:
                return 0

def installAndTrack(system):
    sysID=systemSearch(system)
    taskID, reboot=sysUpgrade(system)
    success=0

    print "Sleeping 30 seconds to allow host to pick up action"
    time.sleep( 30 )
   
    if taskStatus(sysID, taskID, "pickup_time") == 1:
	print "Task picked up successfully"	

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
