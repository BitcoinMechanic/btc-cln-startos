from pathlib import Path
import subprocess,json
r=Path(__file__).resolve().parent
def run(args,**kw):return subprocess.run(args,check=True,**kw)
with (r/'official-ui.squashfs').open('wb') as out:run(['start-cli','s9pk','inspect',str(r/'official-c-lightning_26.6.10_0.s9pk'),'cat','images/x86_64/ui.squashfs'],stdout=out)
run(['unsquashfs','-no-xattrs','-d',str(r/'official-ui-root'),str(r/'official-ui.squashfs')],stdout=subprocess.DEVNULL)
with (r/'official-ui-root.tar').open('wb') as out:run(['tar','-C',str(r/'official-ui-root'),'-cf','-','.'],stdout=out)
run(['docker','import','--change','ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','--change','ENV NODE_VERSION=22.23.4','--change','ENV YARN_VERSION=1.22.22','--change','WORKDIR /app','--change','USER root','--change','ENTRYPOINT ["bash","./scripts/entrypoint.sh"]',str(r/'official-ui-root.tar'),'suitbox-cln-ui:26.6.10'])
