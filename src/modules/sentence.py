import CaboCha
import json


parser = CaboCha.Parser('-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd')


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
        if(token.chunk is not None):
            new_sentence.bunsetsu_size += 1
            new_sentence.bunsetsu_head.append(index)
            new_sentence.dependency.append(token.chunk.link)
    return new_sentence


def read_json(json_text):
    dic = json.loads(json_text)
    new_sentence = Sentence()
    new_sentence.text = dic['text']
    new_sentence.raw_words = dic['raw_words']
    new_sentence.base_form_words = dic['base_form_words']
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
        self.length = 0
        self.bunsetsu_size = 0
        self.bunsetsu_head = list()
        self.dependency = list()
        self.word_category = list()
        self.sub_word_category = list()
    def describe(self):
        return vars(self)
    def to_json(self):
        return json.dumps(self.describe(), ensure_ascii=False)
    def __str__(self):
        return self.text



def main():
    text = "え？私、昨日実は電話来たとき寝てたんだよね。"
    s = read_sentence(text)
    json_s = s.to_json()
    print(json_s)
    print(parser.parseToString(text))

if(__name__ == '__main__'):
    main()
