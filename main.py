import re

def read(path: str):
    with open(path, encoding='utf-8', mode='r') as f:
        txt = f.readlines()
        ret = []
        tmp = ''
        for iraw in txt:
            i = iraw.strip()
            if(i[0] == '＠'):
                continue
            elif('：' in i):
                if(tmp != ''):
                    tmp = re.sub('（.+?）', '', tmp)
                    tmp = re.sub('＜.+?＞', '', tmp)
                    ret.append(tmp)
                tmp = re.sub('.+：', '', i)
            else:
                tmp += i
        tmp = re.sub('（.+?）', '', tmp)
        tmp = re.sub('＜.+?＞', '', tmp)
        ret.append(tmp)
        return ret

if(__name__ == '__main__'):
    res = read('data/nucc/data001.txt')
    for i in res:
        print(i)
