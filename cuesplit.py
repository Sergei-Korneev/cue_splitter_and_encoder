''' 
    Cue file splitter and encoder
    Sergei Korneev [2021]

'''

import subprocess, os, sys
from pathlib import Path
from chardet import detect


'''

Encoding params. I use OPUS with excellent quality.
Use:

bitrate='512k'
lib='aac'

or

bitrate='512k'
lib='flac'

'''

bitrate='400k'
lib='libopus'

cudir=(os.path.abspath(os.getcwd()))

if (sys.version_info.major != 3 and sys.version_info.minor != 8):
    print("This script is tested on Python 3.8!")
    print("You are using Python {}.{}.".format(sys.version_info.major, sys.version_info.minor))
    sys.exit(1)



def __help ():
    print('Cue splitter.\n\nSergei Korneev 2021\n\nUse script.py "path to a .cue file"\n\n')


def __rpunsf (string):
    for ch in ['&','#','\"','\'','*','^',':']:
        if ch in string:
            string=string.replace(ch,'')
    return string


# get file encoding type
def get_encoding_type(file):
    with open(file, 'rb') as f:
        rawdata = f.read()
    return detect(rawdata)['encoding']

def __precheck ():
 
    #check wether we have no parameters or parameters miscount
    #check if an associated wave / flac file exists
    
    if (len(sys.argv)==1) or  not os.path.exists(sys.argv[1]):  
        __help()
        print("\nThe cue file does not exist.")
        sys.exit(1)

    try:
      subprocess.call(["ffmpeg", "-loglevel", "panic"])
    except FileNotFoundError:
      print('Cannot run ffmpeg binary. Try to install it.')
      sys.exit(-1)
 
def __parseacue ():
 
 __precheck()
 cuefile=sys.argv[1]
 cudir=os.path.dirname(cuefile)
 os.chdir(cudir)

 from_codec = get_encoding_type(cuefile)
 
 print('File encoding: '+from_codec+'\n')
# add try: except block for reliability
 try: 
    with open(cuefile, 'r', encoding=from_codec) as f, open(cudir+"/out.cue", 'w', encoding='utf-8') as e:
        text = f.read() # for small files, for big use chunks
        e.write(text)
    cuefile=cudir+"/out.cue"
    #os.remove(srcfile) # remove old encoding file
    #os.rename(trgfile, srcfile) # rename new encoding
 except UnicodeDecodeError:
    print('Decode Error')
 except UnicodeEncodeError:
    print('Encode Error')

 tracks = []
 tr={}
 geninfo = {
        "genre":"Unknown genre",
        "date":"Unknown date",
        "performer":"Unknown performer",
        "comment":"No commentary",
        "title":"Unknown title",
        "file":""
  }

 geninfostart=1

 with open(cuefile) as file:
    for line in file:
      if geninfostart:  
        
        if 'GENRE' in line:
            geninfo["genre"]=' '.join(line.split(' ')[2:]).replace('\n','').replace('"','').lstrip()
        if 'DATE' in line:
            geninfo["date"]=' '.join(line.split(' ')[2:]).replace('\n','').replace('"','').lstrip()
        if 'COMMENT' in line:
            geninfo["comment"]=' '.join(line.split(' ')[2:]).replace('\n','').replace('"','').lstrip()
        if 'PERFORMER' in line:
            geninfo["performer"]=' '.join(line.split(' ')[1:]).replace('\n','').replace('"','').lstrip().title()
        if 'TITLE' in line:
            geninfo["title"]=' '.join(line.split(' ')[1:]).replace('\n','').replace('"','').lstrip().title()
        if 'FILE' in line:
            geninfo["file"]=' '.join(line.split(' ')[1:]).split('"')[1::2]
            geninfostart=0
      else:  

       if 'FILE' in line:
            tr["file"]=' '.join(line.split(' ')[1:]).split('"')[1::2]
       else:
            tr["file"]=geninfo["file"]
       
       if 'TRACK' in line:
           tr={
                 "performer": geninfo["performer"],
                 "comment":"No commentary",
                 "title":"Unknown title",
                 "file":""

           }
           tr["num"]=line.split('TRACK')[1].split(' ')[1]





       if 'TITLE' in line:     
           tr["title"]=' '.join(line.split('TITLE')[1:]).replace('\n','').replace('"','').lstrip().title()
       if 'PERFORMER' in line: 
           tr["performer"]=' '.join(line.split('PERFORMER')[1:]).replace('\n','').replace('"','').lstrip().title()
       if 'INDEX 01' in line:
           index=line.split('INDEX 01')[1].replace('\n','').replace(' ','').split(':')[0:2]
           hour='{:02.0f}'.format(int(int(index[0])/60))
           minute='{:02.0f}'.format(int(int(index[0])%60))
           second=index[1]
           tr["index"]=hour+':'+minute+':'+second
           if tr:
               tracks.append(tr)
 
 if not os.path.exists(geninfo["file"][0]):
        print("Cannot find " + geninfo["file"][0])
        sys.exit(1)
   
 path = Path(__rpunsf(geninfo["performer"]+' - '+geninfo["title"]))
 try:
     path.mkdir(parents=True, exist_ok=True)
 except:
     print("Unable to create output directory.")
     return 1
 for idx, val in enumerate(tracks):
  cmd = ['ffmpeg','-ss',val["index"]] 
  try:
   if  tracks[idx+1]["index"]:
       cmd.append(('-to '+tracks[idx+1]["index"]).split(' ')[0])
       cmd.append(('-to '+tracks[idx+1]["index"]).split(' ')[1])
  except:
       print('\n\nEnd of tracks reached.\n\n')

  if lib == "libopus":
      extension=".opus"
  elif lib == ".aac":
      extension=".m4a"
  else:
     extension=".mp4"

  cmd.extend(
          ['-i',cudir+'/'+str(tracks[idx]["file"][0]),
          '-b:a',bitrate,
          '-c:a',lib,'-vn',
          '-metadata','picture='+cudir+'/'+'cover.jpg',
          '-metadata','title='+tracks[idx]["title"],
          '-metadata','artist='+tracks[idx]["performer"],
          '-metadata','date='+geninfo["date"],
          '-metadata','genre='+geninfo["genre"],
          '-metadata','comment='+geninfo["comment"]+'\nRipped by Cue Splitter (Sergei Korneev, 2021)',
          cudir+'/'+str(path)+'/'+__rpunsf(val["num"]+' - '+val["title"] + extension)])

  print('Encoding:'+'\n\n'+str(cmd)+'\n\n')
  popen = subprocess.Popen(cmd, shell=False)
  popen.wait()
  rc = popen.returncode

__parseacue ()

