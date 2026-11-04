import time, cv2, numpy as np
import wildlife
D='/tmp/claude-0/-home-user-Repo/c9572046-3970-514f-853c-45f37d45ffe9/scratchpad'
ims=[]
for name,fn,idx in (('a',wildlife.shot_a,[0,140]),('b',wildlife.shot_b,[0,75,149])):
    for i in idx:
        t=time.time(); im=fn(i); print(name,i,round(time.time()-t,2),'s',flush=True)
        ims.append(cv2.resize((np.clip(im,0,1)*255).astype(np.uint8),(324,576)))
cv2.imwrite(D+'/wild_test.png', cv2.cvtColor(np.hstack(ims),cv2.COLOR_RGB2BGR))
