import numpy as np
from scipy import interpolate
import datetime
from datetime import datetime
import requests
from requests import HTTPError


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

# TODO: fix automatic detailLevel
def generatePlotVectors(logEvents, detailLevel=20):
    timestampSeconds = []
    weights = []
    for i in logEvents:
        timestampSeconds.append(i.timestamp)
        weights.append(i.threat)
    endTime = timestampSeconds[-1]
    n, x = np.histogram(timestampSeconds, range(0, round(endTime+2*detailLevel + 0.5), detailLevel), weights=weights, density=False)
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
    xnew = np.arange(0, 450, 0.1)
    ynew = []
    for i in xnew:
        ynew.append(poly(i))
    return xnew, ynew

class logConfig:
    logFilePath = ""
    defiance = 5
    mightBonus = False
    stance = "Defensive Stance"
    playerName = ""
    server = ""
    report = ""

    def __init__(self, logFilePath, defiance, mightBonus, stance, playerName, server, report):
        self.logFilePath = logFilePath
        self.defiance = defiance
        self.mightBonus = mightBonus
        self.stance = stance
        self.playerName = playerName
        self.server = server
        self.report = report

    def getThreatFactor(self, spellID):
        factor = 0.8
        if self.stance == "Defensive Stance":
            factor = (1+self.defiance*0.03)*1.3
        if spellID == 20647:
            factor *= 1.25
        elif spellID == 11597 and self.mightBonus:
            factor *= 1.15 # Assuming mightbonus is multiplicative
        return factor

class logData:
    logEvents = []
    fightLength = 419.834
    totalDPS = 0
    totalTPS = 0

def parseDamageEvent(event, config):
    damage = event["amount"]
    spellID = int(event["ability"]["guid"])
    bonusThreat = 0
    if spellID == 23925:
        bonusThreat = 250
    elif spellID == 11601:
        bonusThreat = 315
    elif spellID == 11567:
        bonusThreat = 145
    elif spellID == 11597: # Sunder Armor parry/miss/dodge shows up as damage, subtract threat since the cast has added it
        bonusThreat = -260 #261?

    timestamp = event["timestamp"]/1000
    threat = (damage+bonusThreat)*config.getThreatFactor(spellID)
    targetID = int(event["targetID"])
    if targetID != 21:
        return
    source = 0
    if "sourceID" in event:
        source = int(event["sourceID"])
    if source != 3:
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
    if targetID != 21:
        return
    source = int(event["sourceID"])
    if source != 3:
        return
    spellName = event["ability"]["name"]
    ret = threatEvent(timestamp, threat, damage, targetID, source, spellName)
    return ret

def parseApplyBuffEvent(event, config):
    spellID = int(event["ability"]["guid"])
    source = 0
    if "sourceID" in event:
        source = int(event["sourceID"])
    if source != 3:
        return
    if spellID == 2457:
        config.stance = "Battle Stance"
    elif spellID == 2458:
        config.stance = "Berserker Stance"
    elif spellID == 71:
        config.stance = "Defensive Stance"

def fetchEvents(data, config):
    url = "https://www.warcraftlogs.com:443/v1/report/events/summary/" + config.report #QKnRY3gjtCpZWrMm
    parameters = {
        "api_key": "7c4302d055d8d0f8f0092b04e4be957c",
        "fight": "last",
        "start": "0",
        "end": "500000",
        "sourceid": "3"
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

    threatEvents = []
    for event in events:
        threatInstance = None
        if event["type"] == "cast":
            threatInstance = parseCastEvent(event, config)
        elif event["type"] == "damage":
            threatInstance = parseDamageEvent(event, config)
        elif event["type"] == "applybuff":
            parseApplyBuffEvent(event, config) # update config regarding stances
        if threatInstance is None:
            continue
        else:
            threatEvents.append(threatInstance)

    data.logEvents = threatEvents
    data.totalDPS = round(sum([item.damage for item in data.logEvents])/419.834, 1)
    data.totalTPS = round(sum([item.threat for item in data.logEvents])/419.834, 1)
    return data
