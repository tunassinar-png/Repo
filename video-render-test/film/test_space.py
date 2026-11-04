import sys, time, cv2, numpy as np
import space
D='/tmp/claude-0/-home-user-Repo/c9572046-3970-514f-853c-45f37d45ffe9/scratchpad'
ims=[]
for name,fn,idx in (('earth_a',space.earth_a,[0,140]),('descent',space.descent,[30,70,110,149]),('ascent',space.ascent,[10,70,110,149]),('earth_b',space.earth_b,[0,70,149])):
    for i in idx:
        t=time.time(); im=fn(i); print(name,i,round(time.time()-t,2),'s',flush=True)
        ims.append(cv2.resize((np.clip(im,0,1)*255).astype(np.uint8),(270,480)))
rows=[np.hstack(ims[k:k+7]) for k in range(0,len(ims),7)]
while len(rows[-1][0])<len(rows[0][0]): rows[-1]=np.hstack([rows[-1],np.zeros((480,270,3),np.uint8)])
cv2.imwrite(D+'/space_test.png', cv2.cvtColor(np.vstack(rows),cv2.COLOR_RGB2BGR))
