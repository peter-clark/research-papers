#!/usr/local/bin/python3
import sys
import matplotlib.pyplot as plt
import json
import numpy as np
import glob
from os.path import exists, basename, isfile, isdir, join

def decodeFeatureString(str):
    if not str:
        print("empty str")
        return

    seq = np.zeros(len(str)+1)
    prev = 0
    seq[0] = 0
    for idx, l in enumerate(str):
        if l == 'R':
            val = 0
        elif l == 'U':
            val = 1
        elif l == 'W':
            val = 2
        elif l == 'D':
            val = -1
        elif l == 'B':
            val = -2
        seq[idx+1] = prev + val
        prev = seq[idx+1]

   # print("decode: {} -> {}".format(str, seq))
    return seq

def makePlotOfJson(jsonPath):
    data = None

    if exists(jsonPath):
        with open(jsonPath, 'r') as f:
            data = json.load(f)

    for idx, (ngramLength, sequenceDict) in enumerate(data.items()):
        print("~~~~~~~~~~~~~~~~~~~~~")
        print("ngram length: {}".format(ngramLength))
        totalCount = sum(sequenceDict.values())
        maxCount = max(sequenceDict.values())
        for seq, count in sequenceDict.items():
            weight = float(count)/maxCount
            alpha = weight * weight 

            print("seq: {}; count: {}; weight: {:.4f}".format(seq, count, weight))
            y = decodeFeatureString(seq)
            x = np.arange(len(y))
            plt.plot(x, y, linewidth=weight, alpha=alpha)
        plt.title("{}\n{}-gram; N={}".format(basename(jsonPath), ngramLength, totalCount))
        plt.tight_layout()
        fileStr = 'featureStr_length{}_{}.png'.format(ngramLength, basename(jsonPath))
        pngFolder = 'png'
        filePath = join(pngFolder, fileStr)
        plt.savefig(filePath)
        plt.clf()
        print('saved {}'.format(fileStr))


if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print("need path to json")
        quit()

    for idx, arg in enumerate(sys.argv):
        print ("Argument {}: {}".format(idx, arg))

    jsonPath = sys.argv[1]
    if isfile(jsonPath):
        makePlotOfJson(jsonPath)
    elif isdir(jsonPath):
        jsonList = glob.glob(join(jsonPath, '*.json'))
        for f in jsonList:
            makePlotOfJson(f)

