#!/usr/local/bin/python3

import os
import json
from timeit import default_timer as timer
from datetime import timedelta
import music21 as M
import numpy as np
import xml.etree.ElementTree as ET
print("WELCOME")
# turkish makam scores:
xmlDir = 'SymbTr/MusicXML'
noKeySigDir = os.path.join(xmlDir, 'noKeySig')
jsonDir = 'json'

if not os.path.exists(noKeySigDir):
    os.makedirs(noKeySigDir)

#change to noKeySigDir if you already made the no key sig xmls
fileDir = xmlDir 
#fileDir = noKeySigDir

fileList = [f for f in os.listdir(fileDir) if os.path.isfile(os.path.join(fileDir, f))]
print("file list: length {}".format(len(fileList)))

accidentalDict = {} 

#contains histogram of ngrams
ngramDict = {}
featureStrDict = {}

totFileCnt = len(fileList)
fileCnt = 1

# how much alter is each accidental:
# e.g. 
# tone = 200 # cents
# slashFlatAlter = -(4 * tone / 9)

#alterDict = {
#        "slash-flat": -(4*tone/9),
#

# returns list of ngrams of precise interval sizes
def generate_interval_ngrams(intervalInfoSequence, ngram=1):
    #TODO: initialize to proper size
    intervalSeq = []
    for intervalInfo in intervalInfoSequence:
        interval = intervalInfo["interval"]
        intervalSeq.append(interval)
    temp = zip(*[intervalSeq[i:] for i in range(0,ngram)])
    ans = []
    for n in temp:
        ans.append(n)
    return ans

# takes intervalInfo list
# return list of ngrams of feature strings
def generate_featurestring_ngram(intervalInfoSequence, ngram=1):
    featureCharList = []
    for intervalInfo in intervalInfoSequence:
        interval = intervalInfo["interval"]
        featureChar = getFeatureChar(interval)
        featureCharList.append(featureChar)
    temp = zip(*[featureCharList[i:] for i in range(0,ngram)])
    ans = []
    for n in temp:
        ans.append(n)
    return ans

def are_rotations(str1, str2):
    if len(str1) != len(str2):
        return 0

    s = str1 + str1

    if (s.count(str2) > 0):
        return 1
    else:
        return 0

### make alters for each accidental:
makamAccidentals = ['double-slash-flat', 'flat', 'slash-flat', 'quarter-flat', 'quarter-sharp', 'sharp', 'slash-quarter-sharp', 'slash-sharp']

tone = 200 # cents

slashFlatAlter = -(4 * tone / 9)
doubleSlashFlatAlter = -(8 * tone / 9)
flatAlter = -(5 * tone / 9)
quarterFlatAlter = -(1 * tone / 9)
sharpAlter = (4 * tone / 9) 
slashSharpAlter = (5 * tone / 9)
doubleSlashSharpAlter = (8 * tone / 9)
quarterSlashSharpAlter = (1 * tone / 9)


# sharpAlter = 4 HC
# slashSharpAlter = 5 HC
# doubleSlashSharpAlter = 8 HC
# tone = 9 HC

scale = {'C':0, 'D':200, 'E':400, 'F':500, 'G':700, 'A':900, 'B':1100}

ascendingDict = { # in cents
    'tetra-cargah': [tone,tone,sharpAlter] # HC: 9,9,4
    'penta-cargah': [tone,tone,sharpAlter,tone] # HC: 9,9,4,9
    'tetra-buselik': [tone,sharpAlter,tone] # HC: 9,4,9
    'penta-buselik': [tone,sharpAlter,tone,tone] # HC: 9,4,9
    'tetra-kurdi': [sharpAlter,tone,tone] # HC: 4,9,9
    'penta-kurdi': [sharpAlter,tone,tone,tone] #HC: 4,9,9,9
    'tetra-ussak': [doubleSlashSharpAlter,slashSharpAlter,tone] #HC: 8,5,9
    'penta-ussak': [doubleSlashSharpAlter,slashSharpAlter,tone,tone] #HC: 8,5,9,9
    'tetra-hicaz': [slashSharpAlter,tone+sharpAlter,slashSharpAlter] #HC: 5,12,5
    'penta-hicaz': [slashSharpAlter,tone+sharpAlter,slashSharpAlter,tone] #HC: 5,12,5,9
    'tetra-rast': [tone,doubleSlashSharpAlter,slashSharpAlter] #HC: 9,8,5
    'penta-rast': [tone,doubleSlashSharpAlter,slashSharpAlter,tone] #HC: 9,8,5,9
}


alterDict = {
        'double-slash-flat': doubleSlashFlatAlter,
        'flat': flatAlter,
        'slash-flat': slashFlatAlter,
        'half-flat': quarterFlatAlter, 
        'quarter-flat': quarterFlatAlter,
        'sharp': sharpAlter,
        'slash-quarter-sharp': quarterSlashSharpAlter,
        'slash-sharp': slashSharpAlter,
        'half-sharp': quarterSlashSharpAlter
        }

noteDict = { # [NOTE, OCTAVE, TrueCENTs(aboveC4), EstCENTs(aboveC4), CENTsAboveCinOctave(probably need some +- if running a check against this value)]
    'kaba-cargah': ['C', 4, 0, 0, 0] 
    'yegah': ['D', 4, 204, 200, 200]
    'huseyni-asiran': ['E', 4, 408, 400, 400]
    'acem-asiran': ['F', 4, 498, 500, 500]
    'rast': ['G', 4, 702, 700, 700]
    'dugah': ['A', 4, 906, 900, 900]
    'buselik': ['B', 4, 1109, 1100, 1100]
    'cargah': ['C', 4, 1200, 1200, 0]
    'neva': ['D', 5, 1404, 1400, 200]
    'husenyi': ['E', 5, 1608, 1600, 400]
    'acem': ['F', 5, 1698, 1700, 500]
    'gerdaniye': ['G', 5, 1902, 1900, 700]
    'muhayyer': ['A', 5, 2106, 2100, 900]
    'tiz-buselik': ['B', 5, 2309, 2300, 1100]
    'tiz-cargah': ['C', 6, 2400, 2400, 0]
}
'''
A feature string of a sequence of notes is made from the characters {R, U, W, D, B}.:
    R denotes a repeated note
    U denotes an ascending small interval 
    W denotes an ascending large interval
    D denotes a descending small interval
    B denotes a descending large interval
'''
def generate_feature_string(intervalInfoSeq):
    #    intervalInfoSequence contains { "interval": <cents, float>, "note": <music21.note>}
    s = '' #empty string
    for intervalInfo in intervalInfoSeq:
        interval = intervalInfo["interval"]
        s += getFeatureChar(interval)
    return s

def getFeatureChar(interval):
    if interval <= 1 and interval >= -1:
        return 'R'
    elif interval <= 300 and interval >= 10:
        return 'U'
    elif interval > 300:
        return 'W'
    elif interval >= -300 and interval < -1:
        return  'D'
    elif interval < -300:
        return 'B'
    else:
        print("getFeatureChar shouldnt get here")
        return("X")
    
# analyze only these makam names:
#makamNames = ['rast', 'acemasiran', 'acemkurdi', 'beyati', 'buselik', 'hicaz', 'huseyni', 'huzzam', 'kurdilihicazkar', 'nihavent']
makamNames = ['rast']

# DERIVE From music21.note mutherfucker
#class makamNote(M.note):
#    def __init__(self):
#        self.accidental = ""
#        self.name = ""
#    
#    def __init__(self, accidental, name):
#        self.accidental = accidental
 #       self.name = name

#    def getAlter(self):
#        return 1


for makamName in makamNames:
    fileCnt = 0 
    for f in fileList:
        path = os.path.join(fileDir, f)
        #print("reading file {}/{}: {}".format(fileCnt, totFileCnt, f))

        # just analyze one makam at a time
        if f.split('--')[0] != makamName: 
            fileCnt += 1
            #print("skipping {}".format(f))
            continue

        print("analyzing {}".format(f))

        try:
            s = M.converter.parse(path)

            #print('This score {} contains these {} elements'.format(f, len(s.elements)))
            #for element in s.elements:
            #    print('-', element)
        
        except Exception as e:
            print("error reading {}: {}\n--> going to raw-dog the xml".format(f, e.args))
        
            tree = ET.parse(path)
            root = tree.getroot()

            notes = []
            accidentals = []

            for k in root.iter('key'):
                for ks in k.findall('key-step'):
                    notes.append(ks.text)
                for ka in k.findall('key-accidental'):
                    accidentals.append(ka.text)

            print('The key signature of this score has:')
            for i in range(len(notes)):
                print('-', notes[i], accidentals[i])

            # remove the problematic key signature:
            for att in root.iter('attributes'):
                if att.find('key'):
                    att.remove(att.find('key'))

            newMakamScore = f[:-4] + '--noKeySignature.xml'
            newPath = os.path.join(noKeySigDir, newMakamScore)

            tree.write(newPath)
            try:
                s = M.converter.parse(newPath)
            except Exception as e:
                print("error parsing {}: {}".format(newPath, e.args))
       
            print("accidentals in xml::::::: {}".format(accidentals))
        # list elements in score:
        #print('This score contains these {} elements'.format(len(s.elements)))
        #for element in s.elements:
        #    print('-', element)

        allNotes = s.flat.notes.stream()
        #print("element count: {}".format(len(allNotes.elements)))

        # TODO hack
        # READ THROUGH allNotes
        # READ THROUGH xmlNotes
        # if xmlNotes[idx].accidental:
        #    allNotes[idx].whateverFuckignmetadata = accidental

        #TODO:
        # modify the note.pitch.microtone to fit its accidental
        for n in allNotes: 
            if n.pitch.accidental:
                try:
                    n.pitch.microtone = alterDict[n.pitch.accidental.name]
                except Exception as e:
                    print("error adding microtone: {}".format(e.args))
                    quit()
            #TODO:
            #elif n.whateverfuckinmetadata:
            #    n.pitch.microtone = alterDict[n.pitch.accidental.name]

        intervalInfoList = []
        for note in allNotes:
            if note.pitch.accidental:
                accName = note.pitch.accidental
                if accName not in accidentalDict:
                    accidentalDict[accName] = 1
                else: 
                    accidentalDict[accName] += 1

            ### test
            nextNote = note.next()
            #print("note: {}, next: {}, interval: {}".format(note, nextNote, M.interval.Interval(note, nextNote).cents) )

            #store the interval and the position (offset) in the score of the interval together
            intervalInCents = M.interval.Interval(note, nextNote).cents
            intervalInfo = {"interval": intervalInCents, "startNote": note}
            intervalInfoList.append(intervalInfo)
        
        #print(accidentalDict)

        def convertNgramToStr(ng):
            s = ""
            for ch in ng:
                s += ch
            return s

        # create ngrams and feature string histogram
        for ngramLength in range(3,16):
            #print("finding ngrams of length {}".format(ngramLength))

            # create ngrams of feature strings:
            ngs = generate_featurestring_ngram(intervalInfoList, ngramLength)
            #print("ngrams : {}".format(ngs))
            for ng in ngs:
                featureStr = convertNgramToStr(ng) 
                if ngramLength not in featureStrDict:
                    featureStrDict[ngramLength] = {}
                if featureStr not in featureStrDict[ngramLength]:
                    featureStrDict[ngramLength][featureStr] = 1
                else:
                    featureStrDict[ngramLength][featureStr] += 1

        fileCnt += 1

        #print(featureStrDict) 
        #if (fileCnt > 10):
        #     break

    #fixme:
    sortedFeatureHistogram = {}
    onlyMostCommon = True 
    doNormalize = False
    doCombineRotations = True 
     
    #TODO sum all values -> normalize

    mostCommonCnt = 500
    for ngLen in featureStrDict:
        startTime = timer()
        entryCount = 0
        reversedAndSorted = sorted(featureStrDict[ngLen].items(), key = lambda item: item[1], reverse=True)
        rotationCnt = 0
        for key, value in reversedAndSorted:
            # key: feature string
            # value: how many times the feat. str. appears in the piece
             
            if doCombineRotations:
                for key2, value2 in reversedAndSorted:
                    if are_rotations(key, key2):
                        # dont add the values, dont do this:
                        # value += value2
                        reversedAndSorted.remove((key2,value2))
                        rotationCnt += 1
                        #print("rotation!: {} -- {}: {}+{}={}".format(key, key2, value-value2, value2, value))

            entryCount += 1
            # to only keep entries above this count:
            if onlyMostCommon:
                if entryCount > mostCommonCnt:
                    break
            if ngLen not in sortedFeatureHistogram:
                sortedFeatureHistogram[ngLen] = {}
            sortedFeatureHistogram[ngLen][key] = value
        endTime = timer ()
        elapsedTime = timedelta(seconds=endTime-startTime)
        print("Length {}: removed {} / accepted {} feature strings for rotation in {}".format(ngLen, rotationCnt, entryCount, elapsedTime))
            #print("-- {}: {}".format(key, value))
    
    versionStr = ''
    if onlyMostCommon:
        versionStr += '_top{}'.format(mostCommonCnt)
    if doCombineRotations:
        versionStr += '_no_redundant'

    jsonFile = "{}_ngrams{}.json".format(makamName, versionStr)
    jsonPath = os.path.join(jsonDir, jsonFile) 
    with open(jsonPath, "w") as outfile:
        json.dump(sortedFeatureHistogram, outfile, indent=4)


