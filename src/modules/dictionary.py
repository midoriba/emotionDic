import math
from sentence import Sentence, read_sentence
import json
from pathlib import Path
import datetime
import os


project_dir = Path(__file__).parent.parent.parent


class wordEmotionDictonaryElement:
    def __init__(self, lemma, word_category, update_rate = 0.5):
        self.lemma = lemma
        self.word_category = word_category
        self.update_rate = update_rate
        self.x = 0
        self.y = 0
        self.r = 0
        self.degrees = 0
        self.x_score_list = list()
        self.y_score_list = list()
        self.value_set_times = 0
        self.can_influence = False
        self.is_deleted = False
        self.is_empty = True
    def add_score(self, x, y):
        self.x_score_list.append(x)
        self.y_score_list.append(y)
    def set_value(self, x, y):
        self.x = x
        self.y = y
        self.value_set_times += 1
        self.r = math.sqrt(self.x**2 + self.y**2)
        self.degrees = math.degrees(math.atan2(self.y,self.x))
        self.is_empty = False
    def clear_scores(self):
        self.x_score_list.clear()
        self.y_score_list.clear()
    def init_value(self, x, y):
        self.set_value(x, y)
        self.value_set_times = 0
        self.can_influence = True
    def calc_value(self):
        if(not (self.x_score_list or self.y_score_list)):
            return
        x = 0
        y = 0
        if(self.is_empty):
            x = sum(self.x_score_list) / len(self.x_score_list)
            y = sum(self.y_score_list) / len(self.y_score_list)
        else:
            x = self.x * (1 - self.update_rate) + self.update_rate * sum(self.x_score_list) / len(self.x_score_list)
            y = self.y * (1 - self.update_rate) + self.update_rate * sum(self.y_score_list) / len(self.y_score_list)
        self.set_value(x, y)

    def get_scores(self):
        return [(x, y) for x, y in zip(self.x_score_list, self.y_score_list)]
    def get_value(self):
        return (self.x, self.y)
    def set_never_influence(self):
        self.never_influence = True
    def check(self, min_r):
        if(self.never_influence):
            return 0
        elif(not self.can_influence and self.r >= min_r):
            self.can_influence = True
            return 1
        elif(self.r < min_r):
            self.can_influence = False
            return -1
        else:
            return 0
    def __str__(self):
        ret = f'{self.lemma} ({self.word_category}) ({self.x}, {self.y})'
        if(self.x_score_list and self.y_score_list):
            ret += '['
            ret += ', '.join(f'({x},{y})' for x,y in zip(self.x_score_list, self.y_score_list))
            ret += ']'
        return ret


class wordEmotionDictionary:
    def __init__(self, seed, update_rate=0.5, min_r=0.6, caption=''):
        self.dictionary = dict()
        self.update_rate = update_rate
        self.min_r = min_r
        self.learn_time = 0
        self.size = 0
        self.seed = seed
        self.caption = caption
        with open(project_dir.joinpath('conf','connectorword.json'), encoding='utf-8', mode='r') as f:
            self.connector_words_dictionary = json.load(f)
        # 種表現
        with open(f'{project_dir}/conf/seeds/{seed}', encoding='utf-8', mode='r') as f:
            seed_dic = json.load(f)
            for word_category, words in seed_dic.items():
                for lemma, degree in words.items():
                    rad = math.radians(degree)
                    x = math.cos(rad)
                    y = math.sin(rad)
                    self[lemma, word_category].init_value(x, y)
    def __getitem__(self, keytuple):
        key = f'{keytuple[0]}（{keytuple[1]}）'
        if(key in self.dictionary):
            return self.dictionary[key]
        else:
            self.dictionary[key] = wordEmotionDictonaryElement(keytuple[0], keytuple[1], update_rate=self.update_rate)
            #print(key)
            self.size += 1
            return self.dictionary[key]
    def clear(self):
        self.dictionary.clear()
    def pop(self, key, allow_keyerror = True):
        if(key in self.dictionary):
            return self.dictionary.pop(key)
        elif(allow_keyerror):
            return None
        else:
            raise KeyError
    def calc_values(self):
        for v in self.dictionary.values():
            v.calc_value()
    def check(self):
        for v in self.dictionary.values():
            v.check(self.min_r)
    '''def _read_sentence(self, s: Sentence): #文節頭のみ
        modified_by =  [[] for _ in range(s.bunsetsu_size)]
        for b_influencer_index, influencer_index in enumerate(s.bunsetsu_head[:-1]):
            influencer_word = self[s.base_form_words[influencer_index]]
            #print(s.dependency, influencer_index)
            b_target_word_index = s.dependency[b_influencer_index]
            target_word_index = s.bunsetsu_head[b_target_word_index]
            modified_by[b_target_word_index].append(b_influencer_index) 
            if(influencer_word.can_influence):
                target_word = s.base_form_words[target_word_index]
                self[target_word].add_score(influencer_word.x, influencer_word.y)
                #print(f'{influencer_index}({b_influencer_index}) -> {target_word_index}({b_target_word_index})')
        for b_influencer_index, l in enumerate(modified_by):
            influencer_index = s.bunsetsu_head[b_influencer_index]
            influencer_word = self[s.base_form_words[influencer_index]]
            if(influencer_word.can_influence):
                for b_target_word_index in l:
                    target_word_index = s.bunsetsu_head[b_target_word_index]
                    target_word = s.base_form_words[target_word_index]
                    self[target_word].add_score(influencer_word.x, influencer_word.y)
                    #print(f'{target_word_index}({b_target_word_index}) <- {influencer_index}({b_influencer_index})')'''
    def read_sentence(self, s: Sentence):
        influencer_words_index_list = [] # 影響を与えられる単語のリストインデックス
        # 影響を与えられる単語を探す
        for index, word in enumerate(s.base_form_words):
            if(self[word, s.word_category[index]].can_influence):
                influencer_words_index_list.append(index)
        #print('inf', influencer_words_index_list)
        # 影響を与えられる単語から、スコアを与える
        for influencer_word_index in influencer_words_index_list:
            influencer_word = s.base_form_words[influencer_word_index]
            influencer_word_element = self[influencer_word, s.word_category[influencer_word_index]]
            influencer_word_bunsetsu_index = s.bunsetsu_number[influencer_word_index]
            # 係り
            target_bunsetsu_index = s.dependency[influencer_word_bunsetsu_index]
            target_index = s.bunsetsu_head[target_bunsetsu_index]
            while(target_index < s.length and s.bunsetsu_number[target_index] == target_bunsetsu_index):
                target_word = s.base_form_words[target_index]
                self[target_word, s.word_category[target_index]].add_score(influencer_word_element.x, influencer_word_element.y)
                target_index += 1
                #print(f'{influencer_word} -> {target_word}')
            # 係られ
            for bunsetsu_index, bunsetsu_dependency in enumerate(s.dependency[:-1]):
                if(bunsetsu_dependency == influencer_word_bunsetsu_index):
                    target_index = s.bunsetsu_head[bunsetsu_index]
                    while(s.bunsetsu_number[target_index] == bunsetsu_index):
                        target_word = s.base_form_words[target_index]
                        self[target_word, s.word_category[target_index]].add_score(influencer_word_element.x, influencer_word_element.y)
                        target_index += 1
                        #print(f'{target_word} <- {influencer_word}')
    def learn(self, data):
        for s in data:
            self.read_sentence(s)
        self.calc_values
        self.learn_time += 1
        return 0
    def describe(self):
        return [i for _, i in self.dictionary.items()]
    def to_file(self):
        dt_now = datetime.datetime.now()
        dir_name = 'output_' + dt_now.strftime('%Y%m%d%H%M')
        os.mkdir(f'{project_dir}/output/emodict/{dir_name}')
        with open(f'{project_dir}/output/emodict/{dir_name}/output.csv', encoding='utf-8', mode='w') as f:
            out = 'lemma,word_category,x,y,r,degree,is_empty\n'
            for i, item in self.dictionary.items():
                degree = math.degrees(math.atan2(item.y,item.x))
                out += f'{item.lemma},{item.word_category},{item.x},{item.y},{item.r},{degree},{item.is_empty}\n'
            f.write(out)   
        with open(f'{project_dir}/output/emodict/{dir_name}/meta.json', encoding='utf-8', mode='w') as f:
            meta_dic = {
                "update_rate":self.update_rate,
                "min_r":self.min_r,
                "learn_time":self.learn_time,
                "size":self.size,
                "seed":self.seed,
                "caption":self.caption
            }
            json.dump(meta_dic, f)

if(__name__ == '__main__'):
    print(project_dir)
    text = "え？私、昨日実は電話来たとき寝てたんだよね。"
    s = read_sentence(text)
    d = wordEmotionDictionary()
    d['電話','名詞'].init_value(0.5, 0.5)
    d['とき', '名詞'].init_value(-0.5, 0.5)
    #d.read_sentence(s)
    d.search_connection(s)
    #d.calc_values()
    for i in d.describe():
        print(i)
    #print(d.connector_words_dictionary) 
            