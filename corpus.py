import re
import os
import datetime

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
        ret = {'all':[]}
        tmp = {'speaker':'', 'content':''}
        cnt = 0
        for i in self.txt[self.conversation_index:]:
            if('：' in i):
                if(tmp['content'] != ''):
                    tmp['content'] = re.sub('（.+?）', '', tmp['content'])
                    tmp['content'] = re.sub('＜.+?＞', '', tmp['content'])
                    ret['all'].append(tmp)
                    tmp = {'speaker':'', 'content':''}
                splited_i = i.split('：')
                if(len(splited_i) != 2):
                    print(f'確認してください: "{i}"')
                else:
                    tmp['speaker'], tmp['content'] = splited_i
            elif(i != '＠ＥＮＤ'):
                tmp['content'] += i

        tmp['content'] = re.sub('（.+?）', '', tmp['content'])
        tmp['content'] = re.sub('＜.+?＞', '', tmp['content'])
        ret['all'].append(tmp)
        self.conversation = ret['all']


class word:
    def __init__(self, lemma, value=0):
        self.lemma = lemma
        self.value = value
        self.score = []
        self.isvisited = False
        self.accesscount = 0
    
    def add_score(self, s):
        self.score.append(s)
        return s
    
    def set_value(self, v):
        self.value = v
        self.isvisited = True
        return v

    def reset_score(self):
        self.score = []

    def __str__(self):
        return f'{self.lemma}, {self.value if self.isvisited else "new"}, {self.score}, ({self.accesscount})'

def extract(e: word, x: word):
    return e.value * conjunction(e, x) * reverse(e) * reverse(x)


def conjunction(e, x):
    return 1


def reverse(e):
    return 1


if(__name__ == '__main__'):
    for file in sorted(os.listdir('moddata/nucc'))[:1]:
        cls = Corpus(os.path.join('moddata','nucc', file))
        print(cls.conversation)