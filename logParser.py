import numpy as np
from scipy import interpolate
import datetime
from datetime import datetime


class threatEvent:
    timestamp = 0
    threat = 0
    damage = 0
    target = ""
    source = ""
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
    initialStance = "Defensive Stance"
    playerName = ""
    server = ""

class logData:
    logEvents = []
    fightLength = 0
    totalDPS = 0
    totalTPS = 0
    encounterStart = ""
    encounterEnd = ""

def subtract_timestamps(startTime, endTime):
    startDateTime = datetime.strptime(startTime, "%d/%m %H:%M:%S.%f")
    endDateTime = datetime.strptime(endTime, "%d/%m %H:%M:%S.%f")
    return endDateTime - startDateTime

def parse_dmg_event(timestamp, line, data, config):
    v_line = line.split(",")
    damage = float(v_line[25])
    threat = damage*1.495
    data.totalDPS += damage
    data.totalTPS += threat

    target = v_line[6].strip('"')
    source = v_line[2].strip('"')
    spellName = "Melee"
    ret = threatEvent(timestamp, threat, damage, target, source, spellName)
    return ret

def parse_spell_dmg_event(timestamp, line, data, config):
    v_line = line.split(",")
    damage = float(v_line[28])
    data.totalDPS += damage
    spellID = int(v_line[9])
    bonusThreat = 0
    if spellID == 23925:
        bonusThreat = 250
    elif spellID == 11601:
        bonusThreat = 315
    elif spellID == 11567:
        bonusThreat = 145

    threat = (damage+bonusThreat)*1.495
    data.totalTPS += threat
    target = v_line[6].strip('"')
    source = v_line[2].strip('"')
    spellName = v_line[10].strip('"')
    ret = threatEvent(timestamp, threat, damage, target, source, spellName)
    return ret

def parse_dmg_shield_event(timestamp, line, data, config):
    v_line = line.split(",")
    damage = float(v_line[28])
    data.totalDPS += damage
    data.totalTPS += damage*1.495
    threat = damage*1.495
    target = v_line[6].strip('"')
    source = v_line[2].strip('"')
    spellName = v_line[10].strip('"')
    ret = threatEvent(timestamp, threat, damage, target, source, spellName)
    return ret

def parse_spell_success_event(timestamp, line, data, config):
    v_line = line.split(",")
    spellID = int(v_line[9])
    bonusThreat = 0
    if spellID == 11597:
        bonusThreat = 260 #261?
    threat = bonusThreat*1.495
    data.totalTPS += threat

    damage = 0
    target = v_line[6].strip('"')
    source = v_line[2].strip('"')
    spellName = v_line[10].strip('"')
    ret = threatEvent(timestamp, threat, damage, target, source, spellName)
    return ret


def parse_spell_miss_event(timestamp, line, data, config):
    v_line = line.split(",")
    spellID = int(v_line[9])
    bonusThreat = 0
    if spellID == 11597:
        bonusThreat = -260 #261?
    threat = bonusThreat*1.495
    data.totalTPS += threat

    damage = 0
    target = v_line[6].strip('"')
    source = v_line[2].strip('"')
    spellName = v_line[10].strip('"')
    ret = threatEvent(timestamp, threat, damage, target, source, spellName)
    return ret


def parse_log_line(line, data, config):
    v_line = line.split("  ")
    timestamp = v_line[0]
    line = v_line[1]
    v_line = line.split(",")
    event = v_line[0]
    if event == "ENCOUNTER_START":
        data.encounterStart = timestamp
    if event == "ENCOUNTER_END":
        data.encounterEnd = timestamp
        data.fightLength = subtract_timestamps(data.encounterStart, data.encounterEnd).total_seconds()
    if event != "SWING_DAMAGE_LANDED" and event != "SPELL_DAMAGE" and event != "DAMAGE_SHIELD" and event != "SPELL_CAST_SUCCESS" and event != "SPELL_MISSED":
        return
    source = v_line[2].strip('"')
    target = v_line[6].strip('"')
    if source != config.playerName + "-" + config.server or target != "Onyxia":
        return
    else:
        timestampSec = subtract_timestamps(data.encounterStart, timestamp).total_seconds()
        if event == "SWING_DAMAGE_LANDED":
            data.logEvents.append(parse_dmg_event(timestampSec, line, data, config))
        elif event == "SPELL_DAMAGE":
            data.logEvents.append(parse_spell_dmg_event(timestampSec, line, data, config))
        elif event == "DAMAGE_SHIELD":
            data.logEvents.append(parse_dmg_shield_event(timestampSec, line, data, config))
        elif event == "SPELL_CAST_SUCCESS": # debuffs are spell_aura_applied and applied_dose, casts are casts_success with or withour cast_fail
            data.logEvents.append(parse_spell_success_event(timestampSec, line, data, config))
        elif event == "SPELL_MISSED":
            data.logEvents.append(parse_spell_miss_event(timestampSec, line, data, config))
    return

def parse_combat_log(filePath, data, config):
    f = open(filePath, "r")
    for line in f:
        parse_log_line(line, data, config)
    f.close()
    data.totalTPS = round(data.totalTPS / data.fightLength, 1) # use actual timestamp span instead later
    data.totalDPS = round(data.totalDPS / data.fightLength, 1)
    return data
