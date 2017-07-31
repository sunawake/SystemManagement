#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time   : 2017-07-30 08:40
# @Author : suyang

# REQUIRE python version prior to 3.0 , highly recommend python 3.6.2

import paramiko
import csv
import time


# for your security, PLEASE implement this function! 
def decryptit(usermm):
    return usermm;


# get disk usage information from remote machine.
def checkDiskSpace(ip,port,usermn,usermm,threshold):
    information = "## %s ##" % (ip);
    information = information + "\n" + wordFormat("Caption") + wordFormat("Usage(%)") + wordFormat("Flag");
    database = {};
    # see if we can connect to the server.
    try:
        try:
            connection = paramiko.SSHClient();
            connection.set_missing_host_key_policy(paramiko.AutoAddPolicy());
            connection.connect(ip,port,usermn,usermm);
        except TimeoutError:
            return information + "\nError: Connection Timeout";
        except Exception:
            return information + "\nError: O_o The server may travel to Mars.";
        else:
            # no exception. let's start our work.
            # see the version of operating system.
            osver = getOSVersion(connection);
            # do different work for Windows and Linux
            if osver.lower().find("windows") > -1:
                # operating system is windows
                database = getWindowsUsage(connection);
            elif osver.lower().find("suse") > -1:
                # operating system is Suse
                database = getSuseUsage(connection);
        if len(database) > 0:
            for partition in database.keys():
                infoTmp = wordFormat(partition) + wordFormat(str(database[partition]));
                if database[partition] > threshold:
                    infoTmp = infoTmp + wordFormat("Warning!");
                else:
                    infoTmp = infoTmp + wordFormat(" ");
                information = information + "\n" + infoTmp;
    finally:
        connection.close();
    return information + "\n";
        

# get os version by execute a windows-only commmand.
def getOSVersion(connection):
    osver = "";
    # firstly, see if it is windows. Check Windows Update Service.
    stdin, stdout, stderr = connection.exec_command("sc query \"wuauserv\"");
    # Linux: -bash: sc: command not found.
    if len(stderr.readlines()) > 0:
        osver = "suse linux";
    # windows: SERVICE_NAME: wuauserv ...
    else:
        osver = "windows";
    return osver;


# get windows platform disk usage info.
def getWindowsUsage(connection):
    freespace = 0;
    fullspace = 1;
    database = {};
    # get all partition
    command = "wmic LogicalDisk where \"Description=\'Local Fixed Disk\'\" get Caption /value";
    stdin, stdout, stderr = connection.exec_command(command);
    messageList = stdout.readlines();
    partitionList = [];
    if len(messageList) > 0:
        for index in range(0,len(messageList)):
            message = messageList[index].strip().replace("\r","").replace("\n","");
            if message.startswith("Caption="):
                partitionList.append(message.replace("Caption=",""));
    command = None;
    messageList = None;
    # for every partition, do something.
    if len(partitionList) > 0:
        for partition in partitionList:
            command = "wmic LogicalDisk where \"Caption=\'%s\'\" get FreeSpace,Size /value" % (partition);
            stdin, stdout, stderr = connection.exec_command(command);
            messageList = stdout.readlines();
            if len(messageList) > 0 :
                for index in range(0,len(messageList)) :
                    # output format:
                    # Filesystem 1M-blocks Used Available Use% Mounted-on
                    message = messageList[index].strip().replace("\r","").replace("\n","");
                    if message.startswith("FreeSpace="):
                        freespace = int(message.replace("FreeSpace=",""));
                    elif message.startswith("Size="):
                        fullspace = int(message.replace("Size=",""));
            usage = int((fullspace - freespace) / fullspace * 100);
            database[partition] = usage;
    return database;


# get SUSE platform disk usage info.
def getSuseUsage(connection):    
    freespace = 0;
    fullspace = 1;
    database = {};
    command = "df -BM";
    stdin, stdout, stderr = connection.exec_command(command);
    messageList = stdout.readlines();
    if len(messageList) > 0 :
        if messageList[0].startswith("Filesystem") :
            for index in range(1,len(messageList)) :
                # output format:
                # Filesystem 1M-blocks Used Available Use% Mounted-on
                message = list(filter(None,messageList[index].split(" ")));
                # filesystem = message[0];
                # blocks = message[1];
                # used = message[2];
                # available = message[3];
                usage = int(message[4][:-1]);
                mountPoint = message[5].replace("\n","");
                database[mountPoint] = usage;
    return database;


# add space to the end of string to make it looks good.
def wordFormat(string):
    STRINGLEN = 15;
    if len(string) > STRINGLEN:
        string = string[0:STRINGLEN];
    else:
        for i in range(STRINGLEN - len(string)):
            string = string + " ";
    return string;


def main():
    # which will log.
    information = "";
    # read server access info.
    # csv file format: ip,port,username,password,threshold(%)
    machineList = [];
    try:
        try:
            accessFile = open("remoteMnInfo.csv","r");
        except IOError:
            information = "Error: remoteMnInfo.csv may travel to Mars...";
        else:
            reader = csv.reader(accessFile);
            for row in reader:
                machineList.append(row);
            accessFile.close();
    finally:
        accessFile.close();
    # let us rock!
    if len(machineList) > 1:
        for index in range(1,len(machineList)):
            ip = machineList[index][0];
            # allow comments in the file
            if not ip.startswith("#"):
                port = int(machineList[index][1]);
                usermn = machineList[index][2];
                usermm = decryptit(machineList[index][3]);
                threshold = int(machineList[index][4]);
                info = checkDiskSpace(ip,port,usermn,usermm,threshold);
                information = information + info + "\n\n";
    # write to log file.
    logfileName = "remoteMnLog_" + time.strftime("%Y%m%d%H%M%S", time.localtime()) + ".log";
    try:
        logfile = open(logfileName,"w");
        logfile.write(information);
        logfile.close();
    except IOError:
        print("cannot write to local disk.");


if __name__ == '__main__':
    main();
