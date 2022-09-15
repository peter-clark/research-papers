#!/usr/local/bin/python3

import os
import json
import music21 as M
from music21 import *
import numpy as np
import xml.etree.ElementTree as ET

# turkish makam scores:
xmlDir = '/Users/PeterClark/Documents/Barcelona/Trimester 2/Audio & Music Processing Lab/Project/AMPLab_ngrams/SymbTr/MusicXML'
noKeySigDir = os.path.join(xmlDir, 'noKeySig')
jsonDir = 'json'

if not os.path.exists(noKeySigDir):
    os.makedirs(noKeySigDir)

#change to noKeySigDir if you already made the no key sig xmls
fileDir = xmlDir 

fileList = [f for f in os.listdir(fileDir) if os.path.isfile(os.path.join(fileDir, f))]
print("file list: length {}".format(len(fileList)))

accidentalDict = {} 

#contains histogram of ngrams
ngramDict = {}
featureStrDict = {}

totFileCnt = len(fileList)
fileCnt = 1

def generate_ngrams(noteSeq, ngram=1):
    temp = zip(*[noteSeq[i:] for i in range(0,ngram)])
    ans = []
    for n in temp:
        ans.append(n)
    return ans

'''
A feature string of a sequence of notes is made from the characters {R, U, W, D, B}.:
    R denotes a repeated note
    U denotes an ascending small interval 
    W denotes an ascending large interval
    D denotes a descending small interval
    B denotes a descending large interval
'''
def generate_feature_string(intervalSeq):
    s = '' #empty string
    for interval in intervalSeq:
        if interval <= 1 and interval >= -1:
            s += 'R'
        elif interval <= 300 and interval >= 10:
            s += 'U'
        elif interval > 300:
            s += 'W'
        elif interval >= -300 and interval < -1:
            s += 'D'
        elif interval < -300:
            s += 'B'
        else:
            print("shouldnt get here")
    
    return s

# analyze only these makam names:
makamNames = ['rast', 'acemasiran', 'acemkurdi', 'beyati', 'buselik', 'hicaz', 'huseyni', 'huzzam', 'kurdilihicazkar', 'nihavent']
makamNameTest = ['hicaz']

for makamName in makamNameTest:
    fileCnt = 0 
    for f in fileList:
        path = os.path.join(fileDir, f)
        print("reading file {}/{}: {}".format(fileCnt, totFileCnt, f))

        if f.split('--')[0] != makamName: 
            fileCnt += 1
            # print("skipping {}".format(f))
            continue

        # print("analyzing {}".format(f))

        try:
            s = M.converter.parse(path)

            #print('This score {} contains these {} elements'.format(f, len(s.elements)))
            #for element in s.elements:
            #    print('-', element)
        
        except Exception as e:
            print("error reading {}: {}".format(f, e.args))
        
            tree = ET.parse(path)
            root = tree.getroot()

            notes = []
            accidentals = []
            accidentals_all = []

            # Find key signatures
            for k in root.iter('key'):
                for ks in k.findall('key-step'):
                    notes.append(ks.text)
                for ka in k.findall('key-accidental'):
                    accidentals.append(ka.text)
            print('The key signature of this score has:')
            for i in range(len(notes)):
                print('-', notes[i], accidentals[i])

            # Find all accidentals
            print("The accidentals in this score are:")
            for a in root.iter('accidental'):
                if a.text not in accidentals_all:
                    accidentals_all.append(a.text)
            for i in (range(len(accidentals_all))):
                print('-', accidentals_all[i])

            accidentals_music21 = []


            print('The accidentals parsed by music21 are:')
            for accidental in sorted(accidentals_music21):
                print('-', accidental)

            # remove the problematic key signature:
            for att in root.iter('attributes'):
                if att.find('key'):
                    att.remove(att.find('key'))

            newMakamScore = f[:-4] + '--noKeySignature.xml'
            newPath = os.path.join(noKeySigDir, newMakamScore)

            tree.write(newPath)
            try:
                s = M.converter.parse(newPath)
                            #retrieve all the notes from the score
                nn = s.flat.notes.stream()
                # search for all the accidental names
                for n in nn:
                    if n.pitch.accidental:
                        if n.pitch.accidental.name not in accidentals_music21:
                            accidentals_music21.append(n.pitch.accidental.name)
                # deviation from original pitch of slash-flat in cents
                tone = 200 # cents

                slashFlatAlter = -(4 * tone / 9)
                doubleSlashFlatAlter = -(8 * tone / 9)
                flatAlter = -(5 * tone / 9)
                quarterFlatAlter = -(1 * tone / 9)

                sharpAlter = (4 * tone / 9)
                slashSharpAlter = (5 * tone / 9)
                doubleSlashSharpAlter = (8 * tone / 9)
                quarterSlashSharpAlter = (1 * tone / 9)

                # assign that deviation to notes with slash-flat
                for n in nn:
                    if n.pitch.accidental and n.pitch.accidental.name == 'slash-flat':
                        n.pitch.microtone = slashFlatAlter
                        print("here")
            except Exception as e:
                print("error parsing {}: {}".format(newPath, e.args))
        
        for j in accidentals_music21:
            print("Accidental - {}".format(j))

        # list elements in score:
        #print('This score contains these {} elements'.format(len(s.elements)))
        #for element in s.elements:
        #    print('-', element)

        allNotes = s.flat.notes.stream()
        #print("element count: {}".format(len(allNotes.elements)))

        #TODO:
        # modify the note.pitch.microtone to fit its accidental
        # these are the names of all the accidentals used in makam scores, as contained in the MusicXML files
        makamAccidentals=['double-slash-flat','flat','slash-flat','quarter-flat','quarter-sharp','sharp','slash-quarter-sharp','slash-sharp']
        # create a stream to contained altered notes
        makamNotes = stream.Stream()

        for i in range(len(makamAccidentals)): # create a note per accidental
            try:
                n = s.note.Note()
                n.pitch.accidental = makamAccidentals[i] # add one accidental from the list
                n.addLyric(makamAccidentals[i]) # add the name of the accidental as lyric
                n.addLyric(n.pitch.accidental.name) # add the name used by music21 as lyric
                n.addLyric(n.pitch.alter, applyRaw=True) # add the number of semitones of the accidental as lyric
                makamNotes.append(n)
            except:
                print("music21 doesn't accept {} as accidental".format(makamAccidentals[i]))
        
        #makamNotes.show()

        intervalList = []
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
            intervalList.append(M.interval.Interval(note, nextNote).cents)
            #print("{}".format(M.interval.Interval(note, nextNote).cents))

        # create ngrams and feature string histogram
        for ngramLength in range(3,15):
            #print("finding ngrams of length {}".format(ngramLength))
            ngs = generate_ngrams(intervalList, ngramLength)
            for ng in ngs:
                featureStr = generate_feature_string(ng)
                #print(featureStr)
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
    mostCommonCnt = 20
    for ngLen in featureStrDict:
        entryCount = 0
        for key, value in reversed(sorted(featureStrDict[ngLen].items(), key = lambda item: item[1])):
            entryCount += 1
            # to only keep entries above this count:
            if onlyMostCommon:
                if entryCount > mostCommonCnt:
                    break
            if ngLen not in sortedFeatureHistogram:
                sortedFeatureHistogram[ngLen] = {}
            sortedFeatureHistogram[ngLen][key] = value
            #print("-- {}: {}".format(key, value))
    
    if onlyMostCommon:
        versionStr = '_above{}'.format(mostCommonCnt)
    else:
        versionStr = ''
    jsonFile = "{}_ngrams{}.json".format(makamName, versionStr)
    jsonPath = os.path.join(jsonDir, jsonFile) 
    #with open(jsonPath, "w") as outfile:
    #    json.dump(sortedFeatureHistogram, outfile, indent=4)


