import sys, time, cv2, numpy as np
import city
D='/tmp/claude-0/-home-user-Repo/c9572046-3970-514f-853c-45f37d45ffe9/scratchpad'
t0=time.time()
ims=[]
for name,fn,idx in (('a',city.shot_a,[0,120]),('b',city.shot_b,[0,120])):
    for i in idx:
        t=time.time(); im=fn(i); print(name,i,round(time.time()-t,2),'s',flush=True)
        ims.append(cv2.resize((im*255).astype(np.uint8),(360,640)))
sheet=np.hstack(ims)
cv2.imwrite(D+'/city_test.png', cv2.cvtColor(sheet,cv2.COLOR_RGB2BGR))
print('total',time.time()-t0)
