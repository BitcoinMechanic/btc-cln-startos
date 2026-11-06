"""Filesystem readback helpers; does not read service data volumes."""
import os,stat,hashlib,json,sys
from pathlib import Path
def inventory(root):
 root=Path(root);rows={}
 for parent,dirs,files in os.walk(root):
  for name in dirs+files:
   p=Path(parent)/name;s=p.lstat();rel=str(p.relative_to(root))
   row={'mode':stat.S_IMODE(s.st_mode)}
   if p.is_symlink():row['link']=os.readlink(p)
   elif p.is_file():
    h=hashlib.sha256()
    with p.open('rb') as f:
     for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    row['sha256']=h.hexdigest()
   elif p.is_dir():row['directory']=True
   else:row['special']=stat.S_IFMT(s.st_mode)
   rows[rel]=row
 return rows
if __name__=='__main__':print(json.dumps(inventory(sys.argv[1]),sort_keys=True))
