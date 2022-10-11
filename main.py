import re

def read(path: str):
    with open(path, encoding='utf-8', mode='r') as f:
        txt = f.readlines()
        ret = []
        tmp = {'speaker':'', 'content':''}
        cnt = 0
        for iraw in txt:
            i = iraw.strip()
            if(i[0] == '＠'):
                continue
            elif('：' in i):
                if(tmp['content'] != ''):
                    tmp['content'] = re.sub('（.+?）', '', tmp['content'])
                    tmp['content'] = re.sub('＜.+?＞', '', tmp['content'])
                    ret.append(tmp)
                    tmp = {'speaker':'', 'content':''}
                splited_i = i.split('：')
                if(len(splited_i) != 2):
                    print(f'確認してください: "{i}"')
                else:
                    tmp['speaker'], tmp['content'] = splited_i
            else:
                tmp['content'] += i
        tmp['content'] = re.sub('（.+?）', '', tmp['content'])
        tmp['content'] = re.sub('＜.+?＞', '', tmp['content'])
        ret.append(tmp)
        return ret

if(__name__ == '__main__'):
    res = read('data/nucc/data001.txt')
    print(res)
