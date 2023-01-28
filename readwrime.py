import pandas as pd
import CaboCha
import corpus
import math
import numpy as np
import os

DATA_PATH = 'wrime/wrime-ver1.tsv'
OUTPUT_PATH = 'wrimedic/meand_v2.csv'

wrime_df = pd.read_table(DATA_PATH, encoding='utf-8')

e = {
    "Joy":0,
    "Sadness":240,
    "Anticipation":60,
    "Surprise":90,
    "Anger":140,
    "Fear":110,
    "Disgust":180,
    "Trust":-70
}

def argtoxy(arg, r=1.):
    ret = [
        r * math.cos(arg * math.pi / 180),
        r * math.sin(arg * math.pi / 180)
    ]   
    return ret 

def xytoarg(x, y):
    ret = [
        math.sqrt(x*x + y*y),
        180 * math.atan2(y, x)/ math.pi
    ]
    return ret # 度数法で返す

dic: dict[corpus.WordDicElement] = dict()
parser = CaboCha.Parser()

for i, row in wrime_df[:].iterrows():
    text = row['Sentence']
    point_sum = 0
    tx = 0
    ty = 0
    for i in e.keys():
        p = int(row[f'Avg. Readers_{i}'])
        point_sum += p
        ex, ey = argtoxy(e[i])
        tx += ex * p
        ty += ey * p
    if(point_sum == 0):
        tx = 0
        ty = 0
    else:
        tx = tx/point_sum
        ty = ty/point_sum

    tree = parser.parse(text)
    for tindex in range(tree.size()):
        token = tree.token(tindex)
        features = token.feature.split(',')
        lemma = features[6]
        wordcategory = features[0]
        subwordcategory = features[1]
        if(not lemma in dic.keys()):
            dic[lemma] = corpus.WordDicElement(lemma)
        dic[lemma].add_score([tx, ty])

print('score end')

for key in dic.keys():
    score_len = len(dic[key].score)
    sumx = sum(i[0] for i in dic[key].score)
    sumy = sum(i[1] for i in dic[key].score)
    dic[key].set_value(sumx/score_len, sumy/score_len)
    dic[key].calc_variance()
    dic[key].calc_covariance()

print('variance end')

data = {'lemma':[], 'x':[], 'y':[], 'r':[], 'var_x':[], 'var_y':[], 'cov':[], 'frequency':[]}
for key in dic.keys():
    data['lemma'].append(dic[key].lemma)
    data['x'].append(dic[key].value_x)
    data['y'].append(dic[key].value_y)
    data['r'].append((dic[key].value_x**2 + dic[key].value_y**2)**0.5)
    data['frequency'].append(len(dic[key].score))
    data['var_x'].append(dic[key].variance[0])
    data['var_y'].append(dic[key].variance[1])
    data['cov'].append(dic[key].covariance)

print('data end')

outdf = pd.DataFrame(data)
outdf.loc[outdf['r'] >= 0.7].sort_values('frequency', ascending=False).to_csv(OUTPUT_PATH, encoding="utf-8", index=False)