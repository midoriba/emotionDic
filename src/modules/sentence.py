import CaboCha
import json
from pathlib import Path


parser = CaboCha.Parser('-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd')
project_dir = Path(__file__).parent.parent.parent
with open(project_dir.joinpath('conf', 'connectorword.json'), encoding='utf-8', mode='r') as f:
    connector_dic = json.load(f)
with open(project_dir.joinpath('conf', 'negativeword.json'), encoding='utf-8', mode='r') as f:
    negative_dic = json.load(f)


def read_sentence(text):
    new_sentence = Sentence()
    new_sentence.raw_words.clear()
    new_sentence.base_form_words.clear()
    new_sentence.bunsetsu_head.clear()
    new_sentence.dependency.clear()
    new_sentence.word_category.clear()
    new_sentence.text = text
    new_sentence.bunsetsu_size = 0
    tree = parser.parse(text)
    new_sentence.length = tree.size()
    for index in range(tree.size()):
        token = tree.token(index)
        feature = token.feature.split(',')
        new_sentence.raw_words.append(token.surface)
        new_sentence.base_form_words.append(feature[6])
        new_sentence.word_category.append(feature[0])
        new_sentence.sub_word_category.append(feature[1])
        new_sentence.bunsetsu_number.append(new_sentence.bunsetsu_size)
        if(feature[1] == '接続助詞' and feature[6] in connector_dic['接続助詞']['逆接']):
            new_sentence.reverse_dependency[-1] = True
        if(feature[0] == '助動詞' and feature[6] in negative_dic['助動詞']):
            new_sentence.negative[-1] = True
        if(token.chunk is not None):
            new_sentence.bunsetsu_size += 1
            new_sentence.bunsetsu_head.append(index)
            new_sentence.dependency.append(token.chunk.link)
            new_sentence.reverse_dependency.append(False)
            new_sentence.negative.append(False)
    return new_sentence


def read_json(json_text):
    dic = json.loads(json_text)
    new_sentence = Sentence()
    new_sentence.text = dic['text']
    new_sentence.raw_words = dic['raw_words']
    new_sentence.base_form_words = dic['base_form_words']
    new_sentence.bunsetsu_number = dic['bunsetsu_number']
    new_sentence.length = dic['length']
    new_sentence.bunsetsu_size = dic['bunsetsu_size']
    new_sentence.bunsetsu_head = dic['bunsetsu_head']
    new_sentence.dependency = dic['dependency']
    new_sentence.word_category = dic['word_category']
    new_sentence.sub_word_category = dic['sub_word_category']
    return new_sentence

class Sentence:
    def __init__(self):
        self.text = ''
        self.raw_words = list()
        self.base_form_words = list()
        self.bunsetsu_number = list()
        self.length = 0
        self.bunsetsu_size = 0
        self.bunsetsu_head = list()
        self.dependency = list()
        self.reverse_dependency = list()
        self.negative = list()
        self.word_category = list()
        self.sub_word_category = list()
    def describe(self):
        return vars(self)
    def to_json(self):
        return json.dumps(self.describe(), ensure_ascii=False)
    def __str__(self):
        return self.text



def main():
    text = "売ってたのにあまり綺麗じゃなかった。"
    s = read_sentence(text)
    json_s = s.to_json()
    print(json_s)
    print(parser.parseToString(text))
    print(negative_dic['助動詞'])

if(__name__ == '__main__'):
    main()
