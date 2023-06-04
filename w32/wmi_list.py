#!/usr/bin/env python
"""WMI VSCS Shadow Copy List script."""

import win32com.client
def WMIDateStringToDate(dtmDate):
    """Convert WMI DateString to python Date."""
    if dtmDate == None: return None
    
    strDateTime = ""
    if (dtmDate[4] == 0):
        strDateTime = dtmDate[5] + '/'
    else:
        strDateTime = dtmDate[4] + dtmDate[5] + '/'
    
    if (dtmDate[6] == 0):
        strDateTime = strDateTime + dtmDate[7] + '/'
    else:
        strDateTime = strDateTime + dtmDate[6] + dtmDate[7] + '/'
        strDateTime = strDateTime + dtmDate[0] + dtmDate[1] + dtmDate[2] + dtmDate[3] + " " + dtmDate[8] + dtmDate[9] + "", dtmDate[10] + dtmDate[11] +':' + dtmDate[12] + dtmDate[13]
    return strDateTime

def outputProperty(name, property):
    """Output Shadow Copy property."""
    if property == None: return
    
    print("{0}: {1}".format(name, str(property)))
    
def outputShadowCopy(objItem):
    """Output Shadow Copy Details."""
    outputProperty("Caption", objItem.Caption)
    outputProperty("ClientAccessible", objItem.ClientAccessible)
    outputProperty("Count", objItem.Count)
    outputProperty("Description", objItem.Description)
    outputProperty("DeviceObject", objItem.DeviceObject)
    outputProperty("Differential", objItem.Differential)
    outputProperty("ExposedLocally", objItem.ExposedLocally)
    outputProperty("ExposedName", objItem.ExposedName)
    outputProperty("ExposedPath", objItem.ExposedPath)
    outputProperty("ExposedRemotely", objItem.ExposedRemotely)
    outputProperty("HardwareAssisted", objItem.HardwareAssisted)
    outputProperty("ID", objItem.ID)
    outputProperty("Imported", objItem.Imported)
    outputProperty("InstallDate", WMIDateStringToDate(objItem.InstallDate))
    outputProperty("Name", objItem.Name)
    outputProperty("NoAutoRelease", objItem.NoAutoRelease)
    outputProperty("NotSurfaced", objItem.NotSurfaced)
    outputProperty("NoWriters", objItem.NoWriters)
    outputProperty("OriginatingMachine", objItem.OriginatingMachine)
    outputProperty("Persistent", objItem.Persistent)
    outputProperty("Plex", objItem.Plex)
    outputProperty("ProviderID", objItem.ProviderID)
    outputProperty("ServiceMachine", objItem.ServiceMachine)
    outputProperty("SetID", objItem.SetID)
    outputProperty("State", objItem.State)
    outputProperty("Status", objItem.Status)
    outputProperty("Transportable", objItem.Transportable)
    outputProperty("VolumeName", objItem.VolumeName)

strComputer = "."
objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
objSWbemServices = objWMIService.ConnectServer(strComputer,"root\cimv2")
colItems = objSWbemServices.ExecQuery("SELECT * FROM Win32_ShadowCopy")
for objItem in colItems:
    outputShadowCopy(objItem)