#!/usr/bin/env python
"""WMI VSCS Shadow Copy Deletion script."""

import sys
import win32com.client

shadow_id = sys.argv[1]
strComputer = "."
objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
objSWbemServices = objWMIService.ConnectServer(strComputer,"root\cimv2")
colItems = objSWbemServices.ExecQuery("SELECT * FROM Win32_ShadowCopy WHERE ID=\"{0}\"".format(shadow_id))

for objItem in colItems:
    objItem.Delete_()
