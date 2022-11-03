import re
import os
import datetime
import CaboCha

# TODO: 文節インデックスと単語インデックスを混同しにくくしたい。

class Word:
    reverse_word = ['ない', 'ぬ']
    def __init__(self, lemma: str, wordcategory: str, subwordcategory:str , isbunsetsuhead:bool = False):
        # 見出し語
        self.lemma: str = lemma
        # 文節の頭に当たる単語であるか
        self.isbunsetsuhead: bool = isbunsetsuhead
        # 品詞
        self.wordcategory: str = wordcategory
        # 品詞の詳細
        self.subwordcategory: str = subwordcategory
        # 否定語を同じ文節に含むか
        self.isreverse: bool = self.checkreverseword()
        # 接続詞であるか
        self.isconnector: bool = (self.wordcategory == '接続詞')

    def checkreverseword(self):
        if(self.wordcategory == '助動詞' and self.lemma in self.reverse_word):
            return True
        else:
            return False
    
    def setreverse(self):
        self.isreverse = True

    def __str__(self):
        return self.lemma

class Sentence:
    def __init__(self, text, speaker):
        self.text = text
        self.speaker = speaker
        self.sentence_word_list: list[Word] = list()
        self.bunsetsu_index_list: list[int] = list()
        self.bunsetsu_link_list: list[int] = list()
        self.size: int = 0
        self.bunsetsu_size: int = 0
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
        ret.append(Sentence(spokencontent, speaker))
        self.conversation = ret


class WordDicElement:
    def __init__(self, lemma, value=0):
        self.lemma = lemma
        self.value = value
        self.score = []
        self.isvisited = False
        self.accesscount = 0
        self.isactive = True
    
    def add_score(self, s):
        self.score.append(s)
        return s
    
    def set_value(self, v):
        self.value = v
        self.isvisited = True
        return v

    def reset_score(self):
        self.score = []

    def deactivate(self):
        self.isactive = False

    def __str__(self):
        return f'{self.lemma}, {self.value if self.isvisited else "new"}, {self.score}, ({self.accesscount})'

def extract(e: Word, x: Word, dic: dict):
    #print(e.lemma,'->', x.lemma)
    return dic[e.lemma].value * conjunction(e, x) * reverse(e) * reverse(x)


def conjunction(e, x):
    return 1

def reverse(e: Word):
    if(e.isreverse):
        return -1
    else:
        return 1

if(__name__ == '__main__'):
    '''for file in sorted(os.listdir('moddata/nucc'))[:1]:
        cls = Corpus(os.path.join('moddata','nucc', file))
        print(cls.conversation)'''
    s = Sentence('見かけはきれいだったわ。', 'a01')
    print(s.search_candidate(1))
    #print(s.search_candidate(1))
