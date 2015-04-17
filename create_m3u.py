#!/usr/local/bin/python2
# -*- coding: utf-8 -*-

import os
import fnmatch
import sys
import md5
import shutil
import argparse
import random
import time
import subprocess

debug0=False			# вмикати під час отладки

PlayListFileFull='_full.m3u8'
PlayListFileFullCompat='_full_compat.m3u8'
PlayListFileFullRand='_full_rand.m3u8'
PlayListFileSel='_selected.m3u8'
PlayListFileSelCompat='_selected_compat.m3u8'
PlayListFileSelRand='_selected_rand.m3u8'

exludeLstDir='exclude/'
indiFileListDir='indi/'
fileListFull='full.lst'

symLinksDir='/opt/dump-cache/'

indexOfDir='/usr/local/www/snd/'
indexOfURL='/snd'
URLfull='http://wispy.x.z7z.me:800/snd/m/'

media_collection_dir=[
	'/opt/dump/music',
	'/opt/music'
]

aout=[]
acout=[]
bout={}
cout=[]
ccout=[]
rout=[]
exludeLst=[]
createSelected=False
indi=False
indiPlayLstName=''

def sizeofFmt(num):
#	for x in ['B'] + map(lambda x: x, list('KMGTP')):
	for x in ['B','K','M','G','T','P']:
		if -1024 < num < 1024:
			return "%i%s" % (int(num+0.5), x)
		num /= 1024
	return "%i%s" % (int(num+0.5), x)

def writePlayList(PlayListFile,arrOut):
	if not debug0:
		PlayListFile=os.path.normpath(os.path.join(indexOfDir,PlayListFile))
	out=open(PlayListFile,'w')
	out.write('#EXTM3U\n'+'\n'.join(arrOut)+'\n')
	out.close()

def writePlayListRand(PlayListFile,arrOut):
	rout=arrOut
	random.seed()
	random.shuffle(rout)
	writePlayList(PlayListFile,rout)

def writeIndex():
	eout=[]
	indexOfDirLst=os.listdir(indexOfDir)
	if len(indexOfDirLst) > 0:
		indexOfDirLst=sorted(indexOfDirLst)
		for item in indexOfDirLst:
			if fnmatch.fnmatch(item, "*.m3u8"):
				absPathItem=os.path.normpath(os.path.join(indexOfDir,item))
				if os.path.isfile(absPathItem):
					statinfo = os.stat(absPathItem)
					eout.append('''<tr><td valign="top"><img src="/icons/unknown.gif" alt="[   ]"></td><td><a href="'''+item+'''">'''+item+'''</a>             </td><td align="right">'''+time.strftime('%Y-%m-%d',time.localtime(statinfo.st_mtime))+'''</td><td align="right">'''+sizeofFmt(statinfo.st_size)+'''</td><td>&nbsp;</td></tr>''')
				else:
					break
	indexOf='''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
 <head>
  <title>Index of '''+indexOfURL+'''</title>
 </head>
 <body>
<h1>Index of '''+indexOfURL+'''</h1>
  <table>
   <tr><th valign="top"><img src="/icons/blank.gif" alt="[ICO]"></th><th><a href="'''+indexOfURL+'''">Name</a></th><th><a href="'''+indexOfURL+'''">Last modified</a></th><th><a href="'''+indexOfURL+'''">Size</a></th><th><a href="'''+indexOfURL+'''">Description</a></th></tr>
   <tr><th colspan="5"><hr></th></tr>
<tr><td valign="top"><img src="/icons/back.gif" alt="[PARENTDIR]"></td><td><a href="/">Parent Directory</a>       </td><td>&nbsp;</td><td align="right">  - </td><td>&nbsp;</td></tr>
'''+'\n'.join(eout)+'''
   <tr><th colspan="5"><hr></th></tr>
</table>
</body></html>
'''
	out=open(os.path.normpath(os.path.join(indexOfDir,'index.html')),'w')
	out.write(indexOf)
	out.close()

def getMP3duration(mp3FullN):
	mp3FullN=mp3FullN.replace('`','\`')
	mp3FullN=mp3FullN.replace('"','\"')
	mp3FullN=mp3FullN.replace("'","\'")
	cmdString='/usr/local/bin/mp3info  -p "%S\n" \"'+mp3FullN+'\"'
	p = subprocess.Popen(cmdString, stdout=subprocess.PIPE,shell=True)
	(output, err) = p.communicate()
	p_status = p.wait()

	aIn=output.splitlines()

	if p_status > 0:
		sys.stderr.write('Error in file '+mp3FullN+'\n')
		return(0)
	else:
		return(int(aIn[0]))

def scanMediaDirTree(collectionDir,fileListOut):
	aout=[]
	for rootDir in collectionDir:
		if not os.path.exists(rootDir):
			sys.stderr.write('Directory '+rootDir+' not exists\n')
			continue
		rootDir=os.path.normpath(rootDir)
		# traverse root directory, and list directories as dirs and files as files
		for root, dirs, files in os.walk(rootDir, topdown=False):
			dirs.sort()
			for item in sorted(files):
				if fnmatch.fnmatch(item, "*.mp3"):
					mp3NameFull=os.path.join(root,item)
					mp3duration=getMP3duration(mp3NameFull)
					aout.append(mp3NameFull + '|' + str(mp3duration))

	if len(aout) > 0:
		if os.path.exists(fileListOut):
			shutil.copy(fileListOut,fileListOut+'.bak')
		out=open(fileListOut,'w')
		out.write('\n'.join(aout)+'\n')
		out.close()
		aout=[]

def readExludeFile(exludeFile):
	f=os.path.join(exludeLstDir,exludeFile)
	if not os.path.isfile(f):
		sys.stderr.write('Filename '+f+' is not file\n')
		return
	infile=open(f);
	s=infile.readlines()
	infile.close()
	for i in range(0,len(s)):
		exludeLst.append(s[i].rstrip('\n').strip())

def loadHashesFromIndiFile(indiPlayLstName):
	infile=open(os.path.normpath(os.path.join(indiFileListDir,indiPlayLstName)));
	s=infile.readlines()
	infile.close()
	for f in s:
		indiNameFull=f.rstrip('\n').strip().split('|')[0]
		indiNameHash=md5.new(indiNameFull).hexdigest()+'.mp3'
		if not indiNameHash in bout:
			bout[indiNameHash]=indiNameFull

def createPlayLstEntry(fileList):
	infile=open(fileList);
	s=infile.readlines()
	infile.close()
	for strn in s:
		[mp3NameFull,mp3duration]=strn.strip().rstrip('\n').split('|')
		mp3NamePath=''
		if int(mp3duration) > 30:
			if indi:
				# брудний хак, замінити на отримання даних з MP3
				mp3NamePath=os.path.basename(mp3NameFull)
			else:
				for rootDir in media_collection_dir:
					if mp3NameFull.find(rootDir) == 0:
						mp3NamePath=mp3NameFull.replace(rootDir,'')
						break
			if len(mp3NamePath) < 3:
				sys.stderr.write('Incorrect path "'+mp3NameFull+'", ignored\n')
				continue
			mp3Name4ext=mp3NamePath.lstrip('/').replace('.mp3','  mp3')
			mp3NameWWW=md5.new(mp3NameFull).hexdigest()+'.mp3'
			playListEntry='#EXTINF:' + mp3duration + ',' + mp3Name4ext + '\n' + mp3NameWWW
			aout.append(playListEntry)
			playListEntryCompat='#EXTINF:' + mp3duration + ',' + mp3Name4ext + '\n' + URLfull + mp3NameWWW
			acout.append(playListEntryCompat)
			bout[mp3NameWWW]=mp3NameFull
			if createSelected:
				noXlude=True
				for exludeItem in exludeLst:
					if mp3NameFull.find(exludeItem) == 0:
						noXlude=False
						break
				if noXlude:
					cout.append(playListEntry)
					ccout.append(playListEntryCompat)

def checkSymlink():
	# перевірка наявності сімлінка
	for symLink in bout.keys():
		symLinkAbs=os.path.normpath(os.path.join(symLinksDir,symLink))
		wantCreateSymLink=True
		if os.path.lexists(symLinkAbs):			# 'True' на існуючому, але битому сімлінку
			if not os.path.exists(symLinkAbs):		# 'False' на існуючому, але битому сімлінку ( для перевірки )
				sys.stderr.write('Symlink "'+symLink+'" broken, removed\n')
				os.remove(symLinkAbs)
			elif os.path.islink(symLinkAbs):
				testLink=os.readlink(symLinkAbs)
				if not os.path.isabs(testLink):
					testLink=os.path.normpath(os.path.join(symLinksDir,testLink))
				if bout[symLink] != testLink:
					sys.stderr.write('Symlink "'+symLink+'" points to incorrect source "'+testLink+'", removed\n')
					os.remove(symLinkAbs)
				else:
					wantCreateSymLink=False
			elif os.path.isdir(symLinkAbs):
				sys.stderr.write('Symlink "'+symLink+'" is a directory, removed\n')
				shutil.rmtree(symLinkAbs)
			else:
				sys.stderr.write('Symlink "'+symLink+'" is a file, removed\n')
				os.remove(symLinkAbs)
		if wantCreateSymLink:
			os.symlink(bout[symLink],symLinkAbs)

def checkSymlinkReverse():
	# перевірка на невикористовувані сімлінки
	symLinksDirLst=os.listdir(symLinksDir)
	if len(symLinksDirLst) > 0:
		for symLink in symLinksDirLst:
			if symLink.find(symLinksDir) == 0:
				testLink=symLink.replace(symLinksDir,'')
				symLinkAbs=os.path.normpath(symLink)
			else:
				testLink=symLink
				symLinkAbs=os.path.normpath(os.path.join(symLinksDir,symLink))
			if not testLink in bout:
				os.remove(symLinkAbs)
				sys.stderr.write('Unused symlink "'+symLinkAbs+'" removed\n')

def checkExludeFiles():
	global exludeLst
	box=[]
	errFound=0
	fileChecked=0
	fileSkipped=0
	entrChecked=0
	if not os.path.exists(exludeLstDir):
		sys.stderr.write('Directory '+exludeLstDir+' not exists\n')
	else:
		exludeLstDirFile=os.listdir(exludeLstDir)
		if len(exludeLstDirFile) > 0:
			infile=open(fileListFull);
			listFull=infile.readlines()
			infile.close()
			if len(exludeLst) > 0:
				box=exludeLst
			for exludeFile in exludeLstDirFile:
				exludeLst=[]
				if os.path.exists(os.path.normpath(os.path.join(indiFileListDir,exludeFile+'.lst'))):
					if debug0:
						sys.stderr.write('File "'+exludeFile+'" refer to individual playlist, skipped\n')
					fileSkipped+=1
					continue
				readExludeFile(exludeFile)
				fileChecked+=1
				for exludeItem in exludeLst:
					entryNotFound=True
					entrChecked+=1
					for mp3NameFull in listFull:
						if mp3NameFull.find(exludeItem) == 0:
							entryNotFound=False
							break
					if entryNotFound:
						sys.stderr.write('Unused entry "'+exludeItem+'" in file "'+exludeFile+'"\n')
						errFound+=1
			if len(box) > 0:
				exludeLst=box
				box=[]
			sys.stdout.write('Checked %u entryes in %u files, %u files skipped, ' % (entrChecked,fileChecked,fileSkipped))
			if errFound > 0:
				sys.stdout.write('%u unused entryes found\n' % (errFound))
			else:
				sys.stdout.write('all good\n')

def checkIndiFiles():
	errFound=0
	fileChecked=0
	entrChecked=0
	if not os.path.exists(indiFileListDir):
		sys.stderr.write('Directory '+indiFileListDir+' not exists\n')
	else:
		indiLstDirFile=os.listdir(indiFileListDir)
		if len(indiLstDirFile) > 0:
			for indiFile in indiLstDirFile:
				infile=open(os.path.normpath(os.path.join(indiFileListDir,indiFile)));
				s=infile.readlines()
				infile.close()
				fileChecked+=1
				for item in s:
					indiNameFull=item.rstrip('\n').strip().split('|')[0]
					entrChecked+=1
					if not os.path.exists(indiNameFull):
						sys.stderr.write('Media file "'+indiNameFull+'" in playlist "'+indiFile+'" not exists\n')
						errFound+=1
					elif os.path.isdir(indiNameFull):
						sys.stderr.write('Entry "'+indiNameFull+'" in playlist "'+indiFile+'" is directory, nor file\n')
						errFound+=1
			sys.stdout.write('Checked %u entryes in %u playlists,  ' % (entrChecked,fileChecked))
			if errFound > 0:
				sys.stdout.write('%u erroreneus entryes found\n' % (errFound))
			else:
				sys.stdout.write('all good\n')

def clearIndiFiles(indiFileName):
	global bout
	box=[]
	# remove filelist
	if not os.path.exists(indiFileListDir):
		sys.stderr.write('Directory '+indiFileListDir+' not exists\n')
	else:
		indiFile=os.path.normpath(os.path.join(indiFileListDir,indiFileName+'.lst'))
		if os.path.exists(indiFile):
#			# clear symlinks
#			if len(bout) > 0:
#				box=bout
#				bout=[]
#			loadHashesFromIndiFile(indiFileName+'.lst')
#			for symLink in bout.keys():
#				symLinkAbs=os.path.normpath(os.path.join(symLinksDir,symLink))
#				if os.path.lexists(symLinkAbs):
#					os.remove(symLinkAbs)
#					sys.stderr.write('Unused symlink "'+symLinkAbs+'" removed\n')
#			if len(box) > 0:
#				bout=box
#				box=[]
			os.remove(indiFile)
			sys.stdout.write('Filelist '+indiFileName+'.lst removed\n')
	# remove exclude filelist
	if not os.path.exists(exludeLstDir):
		sys.stderr.write('Directory '+exludeLstDir+' not exists\n')
	else:
		indiFile=os.path.normpath(os.path.join(exludeLstDir,indiFileName))
		if os.path.exists(indiFile):
			os.remove(indiFile)
			sys.stdout.write('Exclude list '+indiFileName+' removed\n')
	# remove playlist
	indiFile=os.path.normpath(os.path.join(indexOfDir,indiFileName+'.m3u8'))
	if os.path.exists(indiFile):
		os.remove(indiFile)
		sys.stdout.write('Playlist '+indiFileName+'.m3u8 removed\n')

# Main

if debug0:
	sys.stderr.write('\n! Debug mode enabled !\n')
	symLinksDir='test/'

parser = argparse.ArgumentParser(description='Create playlists for Media Library')
parser.add_argument('--scan-tree', action='store_true', default=False,help='scan directory tree and build database of media files')
parser.add_argument('--full', action='store_true', default=False,help='generate full playlist')
parser.add_argument('--full-random', action='store_true', default=False,help='generate full randomized playlist')
parser.add_argument('--select', action='store_true', default=False,help='generate selected playlist')
parser.add_argument('--select-random', action='store_true', default=False,help='generate selected randomized playlist')
parser.add_argument('--nosymlinks', action='store_true', default=False,help='nothing to do with symlinks')
parser.add_argument('--index', action='store_true', default=False,help='generate index.html into directory with playlists')
parser.add_argument('--check-exclude', action='store_true', default=False,help='check exclude files for unused entryes')
parser.add_argument('--check-individual', action='store_true', default=False,help='check individual playlists for nor exists files')
parser.add_argument('--folder', action='append', default=[],help='scan given folder(s tree) and create individual playlist (may set many times)')
parser.add_argument('--playlist', default='',help='name of playlist created by "--folder" ( without extension )')
parser.add_argument('--remove-playlist', default='',help='individual playlist ( without extension ) for competely remove')
cmdarg=parser.parse_args()
if not ( cmdarg.scan_tree or cmdarg.full or cmdarg.full_random
		or cmdarg.select or cmdarg.select_random or cmdarg.index
		or cmdarg.check_exclude or cmdarg.check_individual
		or cmdarg.remove_playlist
		or len(cmdarg.folder)>0):
	sys.stderr.write('Nothing to do\n')
	exit(1)

if cmdarg.scan_tree:
	scanMediaDirTree(media_collection_dir,fileListFull)

if len(cmdarg.folder) > 0:
	if len(cmdarg.playlist) == 0:
		if len(cmdarg.folder) > 1:
			sys.stderr.write('Many folder, but not set name of playlist\n')
			exit(1)
		else:
			indiPlayBaseName=os.path.split(cmdarg.folder[0].rstrip('/'))[1].replace(' ','_')
			sys.stderr.write('Name of playlist not set, created automatically ('+indiPlayBaseName+')\n')
	else:
		indiPlayBaseName=cmdarg.playlist
	indiPlayLstName=os.path.normpath(os.path.join(indiFileListDir,indiPlayBaseName+'.lst'))
	scanMediaDirTree(cmdarg.folder,indiPlayLstName)
	indi=True

if indi:
	exludeFile=os.path.normpath(os.path.join(exludeLstDir,indiPlayBaseName))
	if os.path.exists(exludeFile):
		readExludeFile(exludeFile)
elif cmdarg.select or cmdarg.select_random:
	if not os.path.exists(exludeLstDir):
		sys.stderr.write('Directory '+exludeLstDir+' not exists\n')
	else:
		exludeLstDirFile=os.listdir(exludeLstDir)
		if len(exludeLstDirFile) > 0:
			for exludeFile in exludeLstDirFile:
				readExludeFile(exludeFile)

if len(exludeLst) > 0:
	createSelected=True

if indi:
	createPlayLstEntry(indiPlayLstName)
	if len(cout) > 0:
		writePlayList(indiPlayBaseName+'.m3u8',cout)
	elif len(aout) > 0:
		writePlayList(indiPlayBaseName+'.m3u8',aout)
elif cmdarg.full or cmdarg.full_random or cmdarg.select or cmdarg.select_random:
	createPlayLstEntry(fileListFull)
	if len(aout) > 0:
		if cmdarg.full:
			writePlayList(PlayListFileFull,aout)
			writePlayList(PlayListFileFullCompat,acout)
		if cmdarg.full_random:
			writePlayListRand(PlayListFileFullRand,aout)
	if len(cout) > 0:
		if cmdarg.select:
			writePlayList(PlayListFileSel,cout)
			writePlayList(PlayListFileSelCompat,ccout)
		if cmdarg.select_random:
			writePlayListRand(PlayListFileSelRand,cout)

if len(bout) > 0 and not cmdarg.nosymlinks:
	if not indi:
		indiLstDirFile=os.listdir(indiFileListDir)
		if len(indiLstDirFile) > 0:
			for indiPlayLstName in indiLstDirFile:
				if fnmatch.fnmatch(indiPlayLstName,'*.lst'):
					loadHashesFromIndiFile(indiPlayLstName)
	checkSymlink()
	if not indi:
		checkSymlinkReverse()

if cmdarg.index:
	writeIndex()

if cmdarg.check_exclude:
	checkExludeFiles()

if cmdarg.check_individual:
	checkIndiFiles()

if len(cmdarg.remove_playlist) > 0:
	clearIndiFiles(cmdarg.remove_playlist)
