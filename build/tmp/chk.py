import re,sys,os
base='/home/user/workspace/2301106348078317209/All-Men-Are-Brothers/docs/texts/versions/v120'
def check(n):
    s=open(f'{base}/jian/ch{n}.txt',encoding='utf-8').read().split('\n')
    d=open(f'{base}/bai/ch{n}.txt',encoding='utf-8').read().split('\n')
    prob=[]
    if len(s)!=len(d): prob.append(f'LINECOUNT src={len(s)} dst={len(d)}')
    else:
        for i,(a,b) in enumerate(zip(s,d),1):
            if (a.strip()=='')!=(b.strip()==''): prob.append(f'BLANK {i}')
            for ch in '曰矣焉汝吾哉兮':
                if ch in b and not (ch=='曰' and re.search(r'(诗|词|赞|偈|歌|箴|古风)曰',b)):
                    prob.append(f'MARK {i} {ch}')
            if len(a)>40 and a==b: prob.append(f'IDENTICAL(prose?) {i} :: {a[:30]}')
    print(n, 'ratio', round(len(''.join(d))/max(1,len(''.join(s))),3))
    for p in prob[:40]: print('   ',p)
for n in sys.argv[1:]:
    check(n)
