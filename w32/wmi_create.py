#!/usr/bin/env python
"""WMI VSCS Shadow Copy Creation script."""

import win32com.client
import sys

strComputer = "."
wmiSC=win32com.client.GetObject("winmgmts:\\\\.\\root\\cimv2:Win32_ShadowCopy")
createM=wmiSC.Methods_("Create")
createP=createM.InParameters
createP.Properties_['Context'].value="NASRollback"
createP.Properties_['Volume'].value=sys.argv[1]
print( str([(x.name, x.value) for x in createP.Properties_]) )
result=wmiSC.ExecMethod_("Create", createP)
print( str([(x.name, x.value) for x in result.Properties_]) )
