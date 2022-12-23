import re
import os
import datetime
import CaboCha

# wrime用

import math


class PostText:
    def __init__(self, text, speaker, version=0, joy=0, sadness=0, anticipation=0, surprise=0, anger=0, fear=0, disgust=0, trust=0, sentiment=0):
        self.text = text
        self.speaker = speaker
        self.sentence_word_list: list[Word] = list()
        self.bunsetsu_index_list: list[int] = list()
        self.bunsetsu_link_list: list[int] = list()
        self.size: int = 0
        self.bunsetsu_size: int = 0
        self.emot_annotation: dict[int] = {'Joy':joy,'Sadness':sadness,'Anticipation':anticipation,'Surprise':surprise,'Anger':anger,'Fear':fear,'Disgust':disgust,'Trust':trust,'Sentiment':sentiment}
        self.version = version # コーパスのバージョン
        c = CaboCha.Parser()
        tree = c.parse(text)
        # 否定語を含む文節の分節番号のリスト。
        reversebunsetsu = []
        for index in range(tree.size()):
            token = tree.token(index)
            #分節の頭の単語の場合
            isbunsetsuhead = False
            if(token.chunk is not None):
                self.bunsetsu_link_list.append(token.chunk.link)
                self.bunsetsu_index_list.append(index)
                isbunsetsuhead = True
                self.bunsetsu_size += 1
            features = token.feature.split(',')
            lemma = features[6]
            wordcategory = features[0]
            subwordcategory = features[1]
            self.sentence_word_list.append(Word(lemma, wordcategory, subwordcategory, isbunsetsuhead))
            if(self.sentence_word_list[index].isreverse):
                reversebunsetsu.append(self.bunsetsu_size-1)
            self.size += 1
        #print(reversebunsetsu, [])
        for index in reversebunsetsu:
            start_index = self.bunsetsu_index_list[index]
            if(index + 1 >= len(self.bunsetsu_index_list)):
                end_index = self.size
            else:
                end_index = self.bunsetsu_index_list[index+1]
            #print(start_index, end_index)
            for sindex in range(start_index, end_index):
                self.sentence_word_list[sindex].setreverse()
    
    def search_candidate(self, known_index):
        result = set()
        # 既知 -> 未知の係り
        if(known_index != self.size):
            result.add(self.bunsetsu_link_list[known_index])
        # 未知 -> 既知の係り
        for i, b in enumerate(self.bunsetsu_link_list[:-1]):
            if(b == known_index):
                result.add(i)
        return sorted(list(result))

    def info(self):
        return f'{self.speaker}: ' + '|'.join([str(i)+('r' if i.isreverse else '') for i in self.sentence_word_list])

    def __str__(self):
        return f'{self.speaker}: ' + '|'.join([str(i) for i in self.sentence_word_list])
            

# 一つのコーパスファイルを表すクラス
class Corpus:
    def __init__(self, path) -> None:
        self.txt = [] # 全体のテキストデータを行ごとに配列として保存
        self.number = 0 # ファイル番号
        self.mtime = 0 # 会話時間（分）
        self.date = datetime.date(1,1,1) # 会話年月日
        self.place = '' # 会話場所
        self.members = [] # 会話参加者（{id: ID, info: 性別・年代と出身地、居住地}）
        self.relationship = '' # 会話者の関係性
        self.com = ''
        
        self.conversation_index = 0 # 会話の始まる行
        self.conversation = []
        with open(path, encoding='utf-8', mode='r') as f:
            self.txt = [i.strip() for i in f.readlines()]
        self.read_metadata()
        self.read_conversation()
    
    # 冒頭のメタ情報を読み込む
    def read_metadata(self) -> None:
        self.number, self.mtime = map(int, re.search(r'[^０-９0-9]*([０-９0-9]+)（[^０-９0-9]*([０-９0-9]+)分）', self.txt[0]).groups())
        comflag = False
        for index, line in enumerate(self.txt[1:]):
            if(line[0] != '＠'):
                #print(self.number, self.mtime, self.date, self.place)
                #print(self.members)
                if(line[:4] == '％ｃｏｍ'):
                    self.com = line.split('：')[1]
                    comflag = True
                elif(comflag and (not '：' in line)):
                    self.com += line
                    continue
                else:
                    self.conversation_index = index+1
                    return
            attr, value = line[1:].split('：')
            if(attr == '収集年月日'):
                datematch = re.match('[^0-9０-９]*([0-9０-９]+)年[^0-9０-９]*([0-9０-９]+)月[^0-9０-９]*([0-9０-９]+)日',value)
                year, month, day = map(int, datematch.groups())
                self.date = datetime.date(year, month, day)
            elif(attr == '場所'):
                self.place = value
            elif(attr == '参加者の関係'):
                self.relationship = value
            elif(attr[0:3] == '参加者'):
                self.members.append({'id':attr[3:], 'info':value})

    # 会話文を読み込む
    def read_conversation(self):
        if(self.conversation_index == 0):
            return
        ret = []
        speaker = ''
        spokencontent = ''
        cnt = 0
        for i in self.txt[self.conversation_index:]:
            if('：' in i):
                if(spokencontent != ''):
                    spokencontent = re.sub('（.+?）', '', spokencontent)
                    spokencontent = re.sub('＜.+?＞', '', spokencontent)
                    ret.append(Sentence(spokencontent, speaker))
                    speaker = ''
                    spokencontent = ''
                splited_i = i.split('：')
                if(len(splited_i) != 2):
                    print(f'確認してください: "{i}"')
                else:
                    speaker, spokencontent = splited_i
            elif(i != '＠ＥＮＤ'):
                spokencontent += i

        spokencontent = re.sub('（.+?）', '', spokencontent)
        spokencontent = re.sub('＜.+?＞', '', spokencontent)
        ret.append(PostText(spokencontent, speaker))
        self.conversation = ret


class WordDicElement:
    def __init__(self, lemma, value_x=0, value_y=0):
        self.lemma = lemma
        self.value_x = value_x
        self.value_y = value_y
        self.score = []
        self.accesscount = 0
        self.isactive = False # 他の単語のスコアに影響を与えるか
        self.isdeleted = False # 論理削除フラグ
        self.isregistered = False # 感情値が登録されたか
    
    def add_score(self, s):
        self.score.append(s)
        return s
    
    def set_value(self, x, y):
        self.value_x = x
        self.value_y = y
        self.isregistered = True

    def reset_score(self):
        self.score = []

    def activate(self):
        self.isactive = True

    def deactivate(self):
        self.isactive = False

    def delete(self):
        self.isactive = False
        self.isdeleted = True

    def register(self):
        self.isregistered = True

    def activatecheck(self, learntime):
        r, arg = xytoarg(self.value_x, self.value_y)
        #print(r, arg, self.accesscount, r > 0.8, self.accesscount > 100, r > 0.8 and self.accesscount > 100)
        if(r > 0.6 and self.accesscount > 10 * learntime):
            self.activate()
        elif(r <= 0.6):
            self.delete()

    def __str__(self):
        position = f"[{self.value_x}, {self.value_y}]" if self.isregistered else 'null'
        r = (self.value_x**2 + self.value_y**2)**0.5
        return f'{{"lemma":"{self.lemma}","r":{r},"position":{position},"score":{self.score},"accesscount":{self.accesscount},"active":{int(self.isactive)}}}'


def extract(e: Word, x: Word, dic: dict):
    #print(e.lemma,'->', x.lemma)
    return [
        dic[e.lemma].value_x * conjunction(e, x) * reverse(e) * reverse(x),
        dic[e.lemma].value_y * conjunction(e, x) * reverse(e) * reverse(x)
        ]


def conjunction(e, x):
    return 1

def reverse(e: Word):
    if(e.isreverse):
        return -1
    else:
        return 1

def calc_score(cp, argdic):
    dic = argdic.copy()
    linecount = 0
    for line in cp.conversation:
        kk = []
        linecount += 1
        for bindex, b in enumerate(line.bunsetsu_index_list):
            bunsetsu_head = line.sentence_word_list[b]
            try:
                dic[bunsetsu_head.lemma].accesscount += 1
                if(dic[bunsetsu_head.lemma].isactive):
                    candidates = [line.bunsetsu_index_list[i] for i in line.search_candidate(bindex)]
                    for candidate_index in candidates:
                        candidate = line.sentence_word_list[candidate_index]
                        kk.append([bunsetsu_head.lemma, candidate.lemma])
                        try:
                            dic[candidate.lemma].add_score(extract(bunsetsu_head, candidate, dic))
                        except KeyError:
                            newword = WordDicElement(candidate.lemma)
                            newword.add_score(extract(bunsetsu_head, candidate, dic))
                            dic[candidate.lemma] = newword
            except KeyError:
                continue
        if(len(kk) > 0):
            with open('kkout.txt', encoding='utf-8', mode='a') as f:
                f.write(f"[{line.text}]\n")
                f.write('\n'.join([f'{i[0]}->{i[1]}' for i in kk])+'\n')
    return dic


def calc_value(argdic: dict[WordDicElement], learntime: int, alpha: float=0.5, ):
    dic = argdic.copy()
    for key in dic.keys():
        elem = dic[key]
        if(elem.accesscount > learntime*1000):
            pass
        elif(len(elem.score) < 1):
            continue
        elif(elem.isdeleted):
            continue
        elif(elem.isregistered):
            xscore = [i[0] for i in elem.score]
            yscore = [i[1] for i in elem.score]
            newxvalue = sum(xscore)/len(elem.score) * alpha + elem.value_x * (1-alpha)
            newyvalue = sum(yscore)/len(elem.score) * alpha + elem.value_y * (1-alpha)
            dic[key].set_value(newxvalue, newyvalue)
            dic[key].activatecheck(learntime)
        else:
            xscore = [i[0] for i in elem.score]
            yscore = [i[1] for i in elem.score]
            newxvalue = sum(xscore)/len(elem.score)
            newyvalue = sum(yscore)/len(elem.score)
            dic[key].set_value(newxvalue, newyvalue)
            dic[key].activatecheck(learntime)
        dic[key].reset_score()
            
    return dic


if(__name__ == '__main__'):
    '''for file in sorted(os.listdir('moddata/nucc'))[:1]:
        cls = Corpus(os.path.join('moddata','nucc', file))
        print(cls.conversation)'''
    #s = Sentence('見かけはきれいだったわ。', 'a01')
    print(s.search_candidate(1))
