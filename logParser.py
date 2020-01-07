import numpy as np
from scipy import interpolate
import datetime
from datetime import datetime
import requests
from requests import HTTPError

class userConfig:
    reportID = ""
    defiance = 5
    mightBonus = False
    stance = "Defensive Stance"
    fightID = 0
    playerID = 0
    bossID = 0
    fightLength = 0
    startTime = 0
    def __init__(self, reportID, defiance=5, mightBonus=False, stance="Defensive Stance", fightID=0, playerID=0, bossID=0, fightLength=0, startTime = 0):
        self.reportID = reportID
        self.defiance = defiance
        self.mightBonus = mightBonus
        self.stance = stance
        self.fightID = fightID
        self.playerID = playerID
        self.bossID = bossID
        self.fightLength = fightLength
        self.startTime = startTime

    def getThreatFactor(self, spellID):
        factor = 0.8
        if self.stance == "Defensive Stance":
            factor = (1+self.defiance*0.03)*1.3
        if spellID == 20647:
            factor *= 1.25
        elif spellID == 11597 and self.mightBonus:
            factor *= 1.15 # Assuming mightbonus is multiplicative
        return factor

class reportMetaData:
    players = []
    playerIDs = []
    bosses = []
    bossIDs = []
    fightIDs = []
    fightLengths = []
    fightStartTimes = []
    def __init__(self, players, playerIDs, bosses, bossIDs, fightIDs, fightLengths, fightStartTimes):
        self.players = players
        self.playerIDs = playerIDs
        self.bosses = bosses
        self.bossIDs = bossIDs
        self.fightIDs = fightIDs
        self.fightLengths = fightLengths
        self.fightStartTimes = fightStartTimes

# Will be used at a later stage
class fightData:
    threatEvents = []
    fightID = 0
    playerID = 0
    bossID = 0
    fightLength = 0
    startTime = 0

class reportData:
    fightData = [] # all fights
    events = [] # all events 
    totalDPS = 0 # move/remove later
    totalTPS = 0

class threatEvent:
    timestamp = 0
    threat = 0
    damage = 0
    targetID = 0
    sourceID = 0
    spellName = ""
    def __init__(self, timestamp, threat, damage, target, source, spellName):
        self.timestamp = timestamp
        self.threat = threat
        self.damage = damage
        self.target = target
        self.source = source
        self.spellName = spellName

def generatePlotVectors(logEvents, config, detailLevel=0):
    timestampSeconds = []
    weights = []
    startTime = config.startTime
    if detailLevel==0:
        detailLevel=round(config.fightLength/20)
    for i in logEvents:
        timestampSeconds.append(i.timestamp - startTime)
        weights.append(i.threat)
    n, x = np.histogram(timestampSeconds, range(0, round(config.fightLength + 2*detailLevel), detailLevel), weights=weights, density=False)
    n2 = [0]
    x2 = [max(0, x[0] - detailLevel/5.)]
    for i in n:
        n2.append(i/detailLevel)
        n2.append(i/detailLevel)
    for i in range(0, len(x)-1):
        x2.append(x[i] + detailLevel/5.)
        x2.append(x[i+1] - detailLevel/5.)
    dxdy = []
    for i in range(0, len(x2)):
        dxdy.append(0)
    poly = interpolate.CubicHermiteSpline(x2, n2, dxdy)
    xnew = np.arange(0, round(config.fightLength + detailLevel), 0.1)
    ynew = []
    for i in xnew:
        ynew.append(poly(i))
    return xnew, ynew

def parseDamageEvent(event, config):
    damage = event["amount"]
    if damage == 0:
        return
    spellID = int(event["ability"]["guid"])
    bonusThreat = 0
    if spellID == 23925: # Shield Slam
        bonusThreat = 250
    elif spellID == 11601: # Revenge
        bonusThreat = 315
    elif spellID == 11567: # Heroic Strike
        bonusThreat = 145
    elif spellID == 11597: # Sunder Armor parry/miss/dodge shows up as damage, subtract threat since the cast has added it
        bonusThreat = -260 #261?
    elif spellID  == 11581: # Thunder Clap
        bonusThreat = 180

    timestamp = event["timestamp"]/1000
    threat = (damage+bonusThreat)*config.getThreatFactor(spellID)
    targetID = int(event["targetID"])
    if targetID != config.bossID:
        return
    source = 0
    if "sourceID" in event:
        source = int(event["sourceID"])
    if source != config.playerID:
        return
    spellName = event["ability"]["name"]
    ret = threatEvent(timestamp, threat, damage, targetID, source, spellName)
    return ret

def parseCastEvent(event, config):
    bonusThreat = 0
    spellID = int(event["ability"]["guid"])
    if  spellID == 11597:
        bonusThreat = 260 #261?
    threat = bonusThreat*config.getThreatFactor(spellID)

    if not bool(event["sourceIsFriendly"]):
        return

    timestamp = event["timestamp"]/1000
    damage = 0
    targetID = 0
    if "targetID" in event:
        targetID = event["targetID"]
    if targetID != config.bossID:
        return
    source = int(event["sourceID"])
    if source != config.playerID:
        return
    spellName = event["ability"]["name"]
    ret = threatEvent(timestamp, threat, damage, targetID, source, spellName)
    return ret

def parseApplyBuffEvent(event, config):
    spellID = int(event["ability"]["guid"])
    source = 0
    if "sourceID" in event:
        source = int(event["sourceID"])
    if source != config.playerID:
        return
    if spellID == 2457:
        config.stance = "Battle Stance"
    elif spellID == 2458:
        config.stance = "Berserker Stance"
    elif spellID == 71:
        config.stance = "Defensive Stance"
    elif spellID == 11551: # battle shout
        timestamp = event["timestamp"]/1000
        threat = 56*config.getThreatFactor(0) # Assuming only one enemy
        spellName = event["ability"]["name"]
        return threatEvent(timestamp, threat, 0, source, source, spellName)

def parseDebuffEvent(event, config):
    if event["sourceIsFriendly"] == False:
        return
    spellID = int(event["ability"]["guid"])
    source = int(event["sourceID"])
    if source != config.playerID:
        return
    targetID = event["targetID"]
    threat = 0
    if targetID != config.bossID:
        return
    if spellID == 11374: # Gift of Arthas
        threat = 90
    elif spellID == 11556: # Demoralizing Shout
        threat = 42
    threat *= config.getThreatFactor(spellID)
    timestamp = event["timestamp"]/1000
    spellName = event["ability"]["name"]
    return threatEvent(timestamp, threat, 0, targetID, source, spellName)

def parseEnergizeEvent(event, config):
    spellID = int(event["ability"]["guid"])
    source = int(event["sourceID"])
    if source != config.playerID:
        return
    else: # We know we gained rage
        spellName = event["ability"]["name"]
        timestamp = event["timestamp"]/1000
        amount = event["resourceChange"] - event["waste"]
        threat = amount*config.getThreatFactor(0) # Assuming only one enemy
        return threatEvent(timestamp, threat, 0, source, source, spellName + " (Rage Gain)")

def fetchFightInfo(config):
    url = "https://classic.warcraftlogs.com:443/v1/report/fights/" + config.reportID
    parameters = {
        "api_key": "7c4302d055d8d0f8f0092b04e4be957c"
    }
    fights = []
    friendlies = []
    enemies = []
    try:
        response = requests.get(url, params=parameters)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')

    fights = response.json()["fights"]
    friendlies = response.json()["friendlies"]
    enemies = response.json()["enemies"]

    players = [item["name"] for item in friendlies]
    playerIDs = [item["id"] for item in friendlies]
    bosses = [item["name"] for item in fights if item["boss"] != 0 and item["kill"] == True]
    bossIDs = []
    for bossName in bosses:
        bossIDs.append([item["id"] for item in enemies if item["type"] == "Boss" and item["name"] == bossName][0])
    fightIDs = [item["id"] for item in fights if item["boss"] != 0 and item["kill"] == True]
    fightStartTimes = [item["start_time"]/1000 for item in fights if item["boss"] != 0 and item["kill"] == True]
    fightLengths = [(item["end_time"] - item["start_time"])/1000 for item in fights if item["boss"] != 0 and item["kill"] == True]

    #print(players, playerIDs, bossIDs, bosses, fightIDs, fightLengths, fightStartTimes)

    ret = reportMetaData(players, playerIDs, bosses, bossIDs, fightIDs, fightLengths, fightStartTimes)
    return ret

def fetchEvents(reportData, config):
    url = "https://www.warcraftlogs.com:443/v1/report/events/summary/" + config.reportID 
    #print("fight ID: " + str(config.fightID) + "  fightLength: " + str(config.fightLength) + "  playerID: " + str(config.playerID) + "  bossID: " + str(config.bossID))
    parameters = {
        "api_key": "7c4302d055d8d0f8f0092b04e4be957c",
        "fight": config.fightID,
        "start": int(config.startTime*1000),
        "end": int(config.startTime*1000 + config.fightLength*1000),
        "sourceid": config.playerID
    }
    events = []
    try:
        response = requests.get(url, params=parameters)
        events = response.json()["events"]
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')

    #print("n events: " + str(len(events)))
    threatEvents = []
    for event in events:
        threatInstance = None
        if event["type"] == "cast":
            threatInstance = parseCastEvent(event, config)
        elif event["type"] == "damage":
            threatInstance = parseDamageEvent(event, config)
        elif event["type"] == "applybuff":
            parseApplyBuffEvent(event, config) # update config regarding stances AND BATTLE SHOUT
        elif event["type"] == "applydebuff" or event["type"] == "refreshdebuff":
            threatInstance = parseDebuffEvent(event, config) # Gift of Arthas
        elif event["type"] == "energize":
            threatInstance = parseEnergizeEvent(event, config) # Rage Gains
        if threatInstance is None:
            continue
        else:
            threatEvents.append(threatInstance)
    #print("threat events: " + str(len(threatEvents)))

    reportData.events = threatEvents
    reportData.totalDPS = round(sum([item.damage for item in reportData.events])/config.fightLength, 1)
    reportData.totalTPS = round(sum([item.threat for item in reportData.events])/config.fightLength, 1)
    return reportData
