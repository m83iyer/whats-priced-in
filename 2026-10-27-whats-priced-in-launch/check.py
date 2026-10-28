import re,sys,pathlib
BAN=["game-changer","game changer","revolutionary","unlock","delve","supercharge","dive in","in today's","10x","must-see","you won't believe","buy","sell","target price","price target","strong buy"]
bad=0
for f in ["post-draft.md","thread-alt.md"]:
    t=pathlib.Path(__file__).with_name(f).read_text()
    for name,body in re.findall(r"<!-- POST:(\S+) -->\n(.*?)\n<!-- /POST -->",t,re.S):
        n=len(body); low=body.lower()
        xw=sum(1 if (ord(c)<=0x10FF or 0x2000<=ord(c)<=0x200D or 0x2010<=ord(c)<=0x201F or 0x2032<=ord(c)<=0x2037) else 2 for c in body.replace("REPO_URL",""))+23*body.count("REPO_URL")+sum(23-len(u) for u in re.findall(r"https://\S+",body))
        hits=[b for b in BAN if re.search(r"\b"+re.escape(b)+r"\b",low)]
        url="REPO_URL" in body or re.search(r"https://\S+",body)
        flag="OK" if n<=280 and xw<=280 and not hits else "FAIL"
        if flag=="FAIL": bad+=1
        print(f"{f}:{name} chars={n} x_weighted={xw} banned={hits or '-'} url={'yes' if url else 'no'} {flag}")
print("ALL MATCH" if not bad else f"MISMATCH {bad}"); sys.exit(1 if bad else 0)
