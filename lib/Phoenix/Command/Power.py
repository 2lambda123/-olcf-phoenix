#!/usr/bin/env python
"""Power management"""
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import sys
import logging

from ClusterShell.NodeSet import NodeSet
from jinja2 import Template
from jinja2 import Environment
import re
import copy
import importlib
import ipaddress
import Phoenix
from Phoenix.System import System

class Power(command):
    def __init__(self, name):
        pass

    def run_command(self, client):
        try:
            #client.output("Running command %s for node %s" % (client.command, self.attr['name']))
            if isinstance(client.command, list):
                command = client.command[0]
                args = client.command[1:]
            else:
                command_parts = client.command.split()
                command = command_parts[0]
                args = command_parts[1:]
            if command == "power":
                try:
                    if args[0][0:3] == "pdu":
                        # Call the "normal" power commands (without pdu* prefix) against the PDU class"
                        args[0] = args[0][3:]
                        oobkind = "pdu"
                        oobtype = self['pdutype']
                        oobcls = _load_oob_class("pdu", oobtype)
                    else:
                        oobkind = "bmc"
                        oobtype = self['bmctype']
                except KeyError:
                    client.output("%stype not set" % oobkind, stderr=True)
                    rc=1
                else:
                    oobcls = _load_oob_class(oobkind, oobtype)
                    rc = oobcls.power(self, client, args)
            elif command == "firmware":
                oob = _load_oob_class("bmc", self['bmctype'])
                rc = oob.firmware(self, client, args)
            elif command == "inventory":
                oob = _load_oob_class("bmc", self['bmctype'])
                rc = oob.inventory(self, client, args)
            elif comand == "discover":
                oob = _load_oob_class("bmc", self['discovertype'])
                rc = oob.discover(self, client, args)
            else:
                client.output("Unknown command '%s'" % command, stderr=True)
                rc = 1
            client.mark_command_complete(rc=rc)
        except Exception as e:
            client.output("Error running command: %s - %s" % (str(e), e.args), stderr=True)
            client.mark_command_complete(rc=1)

def _load_oob_class(oobtype, oobprovider):
    if oobprovider is None:
        logging.debug("Node does not have %stype set", oobtype)
        raise ImportError("Node does not have %stype set" % oobtype)
    logging.debug(oobprovider)
    #classname = oobprovider.lower().capitalize() + oobtype.lower().capitalize()
    classname = oobprovider.lower().capitalize()
    modname = "Phoenix.OOB.%s" % classname

    # Iterate over a copy of sys.modules' keys to avoid RuntimeError
    if modname.lower() not in [mod.lower() for mod in list(sys.modules)]:
        # Import module if not yet loaded
        __import__(modname)


    # Get the class pointer
    try:
        return getattr(sys.modules[modname], classname + oobtype.lower().capitalize())
    except:
        raise ImportError("Could not find class %s" % classname + oobtype.lower().capitalize())
