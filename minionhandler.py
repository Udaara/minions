from __future__ import print_function
import httplib2
import os
import json
import time
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from apiclient import errors
import base64
import email
from apiclient import errors
from datetime import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'

#Authorize User and Environment
def get_credentials():

    credential_dir = os.getcwd() + '/credentials'
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)                             
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('gmail', 'v1', http=http)
user_id = '********@gmail.com'

#Get mail for a given Label
def ListMessagesWithLabels(label_ids=[]):

  try:
    response = service.users().messages().list(userId=user_id,
                                               labelIds=label_ids).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id,
                                                 labelIds=label_ids,
                                                 pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError, error:
    """print 'An error occurred: %s' % error"""

#Get message body
def GetMessage(msg_id):

  try:
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()

    """print 'Message snippet: %s' % message['snippet']"""

    return message
  except errors.HttpError, error:
    """print 'An error occurred: %s' % error"""

#Change mail label
def CreateMsgLabels():

  return {'removeLabelIds': ['UNREAD']}

#Wait 10 minutes after restarting all minions
def WatchDogDodge(message):

    textArray = message.split(' ')
    logfile = 'minion_automation.log'
    f = open(logfile, 'a')
    hostip = ""

    with open("minions.json") as json_file:
        json_data = json.load(json_file)
        dct = json_data

    bubbles = set()

    for key in dct.keys():

        bubble = key 
        bubbles.add(bubble)

        failedStatus = message.find("degraded")
        hostip=""
        if failedStatus == -1:
            print ("Minion Alert! Not a failure!")
            f.write("Minion Alert! Not a failure \t\t %s \n" % (str(datetime.now())))
            f.close()
        return 'Moving On'

#Detect and reboot failed minions
def DetectFailedMessages(message):

    textArray = message.split(' ')
    logfile = 'minion_automation.log'
    f = open(logfile, 'a')
    hostip = ""

    with open("minions.json") as json_file:
        json_data = json.load(json_file)
        dct = json_data

    bubbles = set()

    for key in dct.keys():
        
        bubble = key 
        bubbles.add(bubble)

    failedStatus = message.find("degraded")
    hostip=""
    if failedStatus == -1:
        print ("Minion Alert! Not a degrade!")
        f.write("Minion Alert! Not a degrade \t\t %s \n" % (str(datetime.now())))
        f.close()
        return 'Moving On'

    else:
        for loc in bubbles:  
            for key in textArray:
                #keyIndex = key.find(loc)
                
                print("Key ==> "+key)
                print("Loc ==> "+loc)
                if key.lower() == "London".lower():
                    londonIndex = textArray.index(key)
                    nextString = textArray[londonIndex+1]
                    key = key +' '+ nextString
                    print (key)

                if key.lower() == loc.lower():
                    print(loc);
                    locName = key;
                    locIPArray = dct[locName]

        with open("config.json") as json_file:
            json_data = json.load(json_file)
            dct = json_data
        
        for key in dct.keys():
            host = key
            pwd = dct[key]
            
            for locIP in locIPArray:
                for k, v in locIP.items():
                    if host == v:
                        try:
                                f = open(logfile, 'a')
                                os.system("fab -H %s -p '%s' taskA" % (v,pwd))
                                f.write("Reboot initiated for %s \t\t %s \n" % (v,str(datetime.now())))
                                f.write("Waiting for 20 seconds... \n")
                                f.close()
                                time.sleep(20)
                        except:
                                f = open(logfile,'a')
                                f.write("Exception raised! \t\t %s \n" % str(datetime.now()))
                                f.close()
                                print ("Exception raised")
                    else:
                       #f = open(logfile, 'a')
                       # f.write("Your host is not known ==> %s \n" % host )
                       print ("Your host is not known ==> %s \n " % host)
                       #f.close()

        print ("Alert from Minion "+locName+", Minion degraded!")
        endTime = datetime.datetime.now() + datetime.timedelta(minutes=1)
        while True:
            if datetime.datetime.now() >= endTime:
                f = open(logfile,'a')
                f.write("Waited for 10 minutes. Switch back to normal monitoring. \t\t %s \n"% (str(datetime.now())))
                f.close()
                break
            else:
                res = ListMessagesWithLabels(label_ids=['UNREAD'])
                logfile = 'minion_automation.log'
                if(res==[]):
                    f = open(logfile,'a')
                    f.write("Waiting 10 minutes after the recovery \t\t %s \n"% (str(datetime.now())))
                    f.close()
                else:
                    """Get UNREAD Mail Contents"""
                    res2 = GetMessage(res[0]['id'])
                    message = res2['snippet']
                    """Set UNREAD to READ"""
                    changeVal = CreateMsgLabels()
                    res4 = ModifyMessage(res[0]['id'], changeVal)
                    print(res4)
                    """Reboot the Minions"""
                    res3 = WatchDogDodge(message)
                    print (res3)
                    time.sleep(10)
        return 'Reboot Initiated'
                
#Modify Mail status
def ModifyMessage(msg_id, msg_labels):

  try:
    message = service.users().messages().modify(userId=user_id, id=msg_id,
                                                body=msg_labels).execute()

    label_ids = message['labelIds']
    return 'Changed mail status to Read'

  except errors.HttpError, error:
    print ('An error occurred: %s' % error)
    

"""Get UNREAD Mail IDs"""
while True:
    res = ListMessagesWithLabels(label_ids=['UNREAD'])
    logfile = 'minion_automation.log'
    if(res==[]):
        f = open(logfile,'a')
        f.write("No Unread Mails found \t\t %s \n"% (str(datetime.now())))
        f.close()
        print ("No Unread Mails found")
    else:
        """Get UNREAD Mail Contents"""
        res2 = GetMessage(res[0]['id'])
        message = res2['snippet']
        """Set UNREAD to READ"""
        changeVal = CreateMsgLabels()
        res4 = ModifyMessage(res[0]['id'], changeVal)
        print(res4)
        """Reboot the Minions"""
        res3 = DetectFailedMessages(message)
        print (res3)
    time.sleep(10)
