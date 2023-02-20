import traceback
import math

class wordEmotionDictonaryElement:
    def __init__(self, lemma, update_rate = 0.5):
        self.lemma = lemma
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
    def add_score(self, x, y):
        self.x_score_list.append(x)
        self.y_score_list.append(y)
    def set_value(self):
        self.x = self.x * (1 - self.update_rate) + self.update_rate * sum(self.x_score_list) / len(self.x_score_list)
        self.y = self.y * (1 - self.update_rate) + self.update_rate * sum(self.y_score_list) / len(self.y_score_list)
        self.value_set_times += 1
        self.x_score_list.clear()
        self.y_score_list.clear()
        self.r = math.sqrt(self.x**2 + self.y**2)
        self.degrees = math.degrees(math.atan2(self.y,self.x))
    def get_scores(self):
        return [(x, y) for x, y in zip(self.x_score_list, self.y_score_list)]
    def get_value(self):
        return (self.x, self.y)
    def __str__(self):
        return f'{self.lemma} ({self.x}, {self.y})'


class wordEmotionDictionary:
    def __init__(self, update_rate=0.5, min_r=0.6):
        self.dictionary = dict()
        self.update_rate = update_rate
        self.min_r = min_r
        self.learn_time = 0
    def __getitem__(self, key):
        if(key in self.dictionary):
            return self.dictionary[key]
        else:
            self.dictionary[key] = wordEmotionDictonaryElement(key, update_rate=self.update_rate)
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
    def calc_scores(self):
        for key in self.dictionary:
            self.dictionary[key].set_value()
    
            

