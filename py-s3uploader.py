import argparse,os,time,math,re
from threading import Thread
from boto.s3.connection import S3Connection
from boto.s3.key import Key

"""
With this class / command you can upload a directory recursively,
or a single level deep, or just a single file.
"""

"""
Upload a directory:
s3uploader.py \
--api "MYAPIKEY" \
--secret "MYSECRETKEY" \
--bucket "mybucket" \
--bucketpath "path/on/bucket/" \
--source "local/path/" \
--recursive \
--ignoredates \
--threads 3
"""

"""
Upload a file:
s3uploader.py \
--api "MYAPIKEY" \
--secret "MYSECRETKEY" \
--bucket "mybucket" \
--bucketpath "path/on/bucket/myfile.json" \
--source "local/path/myfile.json" \
--ignoredates
"""

class S3Uploader:
	api = None
	secret = None
	dryrun = False
	filetype_meta = {} #=> dictionary of array of dictionaries. Example: ({"css":[{"content-type":"text/css"}]})
	
	def __init__(self,api,secret):
		self.api = api
		self.secret = secret
		self._init_default_metas()

	def _init_default_metas(self):
		self.set_metadata_for_filetype("css",{"Content-Type":"text/css"})
		self.set_metadata_for_filetype("html",{"Content-Type":"text/html"})
		self.set_metadata_for_filetype("js",{"Content-Type":"application/javascript"})
		self.set_metadata_for_filetype("jpg",{"Content-Type":"image/jpeg"})
		self.set_metadata_for_filetype("jpeg",{"Content-Type":"image/jpeg"})
		self.set_metadata_for_filetype("json",{"Content-Type":"application/json"})
		self.set_metadata_for_filetype("mp4",{"Content-Type":"video/mp4"})
		self.set_metadata_for_filetype("ogg",{"Content-Type":"application/ogg"})
		self.set_metadata_for_filetype("otf",{"Content-Type":"application/x-font-otf"})
		self.set_metadata_for_filetype("png",{"Content-Type":"image/png"})
		self.set_metadata_for_filetype("txt",{"Content-Type":"text/plain"})
		self.set_metadata_for_filetype("webm",{"Content-Type":"video/webm"})
		self.set_metadata_for_filetype("xml",{"Content-Type":"application/xml"})
		self.set_metadata_for_filetype("zip",{"Content-Type":"application/zip"})

	def set_metadata_for_filetype(self,filetype,meta):
		mta = self.get_metadata_for_filtetype(filetype)
		if mta:
			mta.append(meta)
		else:
			self.filetype_meta[filetype] = []
			self.filetype_meta[filetype].append(meta)

	def get_metadata_for_filtetype(self,filetype):
		return self.filetype_meta.get(filetype,None)

	def upload_dir(self,bucket,bucketbasepath,dirsource,recursive,threadcount,ignoredates):
		files = []
		if recursive: files = self._get_files_recursive(bucketbasepath,dirsource)
		else: files = self._get_files(bucketbasepath,dirsource)
		threads = []
		if(threadcount > 1):
			c = math.ceil(float(len(files))/threadcount)
			thread_pairs = []
			for i in range(int(threadcount)):
				thread_pairs.append([])
				for j in range(int(c)):
					try:
						pair = files.pop()
						thread_pairs[i].append(pair)
					except Exception as e:
						pass
			for i in range(len(thread_pairs)):
				pairs = thread_pairs[i]
				thread = Thread(target=self._upload_dir,args=(bucket,bucketbasepath,dirsource,pairs,ignoredates))
				threads.append(thread)
				thread.start()
		elif threadcount == 1:
			thread = Thread(target=self._upload_dir,args=(bucket,bucketbasepath,dirsource,files,ignoredates))
			threads.append(thread)
			thread.start()
		for thread in threads:
			thread.join()

	def upload_file(self,bucket,bucketpath,filepath,ignoredates):
		s3connection = S3Connection(self.api,self.secret)
		s3bucket = s3connection.get_bucket(bucket)
		fullpath = os.path.relpath(os.path.abspath(filepath))
		filename = fullpath.split("/")[-1]
		bucketfile = "%s/%s" % (bucketpath,filename)
		bucketfile = re.sub("/%s$"%filename,"",bucketfile)
		self._upload_file(s3connection,s3bucket,fullpath,bucketfile,ignoredates)

	def _upload_file(self,connection,bucket,localfile,bucketfile,ignoredates):
		s3key = bucket.get_key(bucketfile)
		if not s3key:
			s3key = Key(bucket)
			s3key.key = bucketfile
		s3date = s3key.get_metadata("date")
		if s3date: s3date = int(s3date)
		lcdate = int(os.path.getmtime(localfile))
		upload = False
		if not s3date: upload = True
		if s3date and lcdate > s3date: upload = True
		if ignoredates: upload = True
		if upload:
			if self.dryrun: print "dry-run. %s : %s => %s" % (bucket.name,localfile,bucketfile)
			else: print "%s : %s => %s" % (bucket.name,localfile,bucketfile)
			filetype = localfile.split(".")[-1]
			meta = self.get_metadata_for_filtetype(filetype)
			if meta:
				for metadata in meta:
					for key in metadata:
						print "    => metdata: %s:%s" % (key,metadata[key])
						if not self.dryrun:
							s3key.set_metadata(key,metadata[key])
			if not self.dryrun:
				s3key.set_metadata("date",str(int(time.time())))
				s3key.set_contents_from_filename(localfile)
	
	def _upload_dir(self,bucket,bucketpath,dirsource,files,ignoredates):
		s3connection = S3Connection(self.api,self.secret)
		s3bucket = s3connection.get_bucket(bucket)
		for pair in files:
			localfile = pair[0]
			bucketfile = pair[1]
			self._upload_file(s3connection,s3bucket,localfile,bucketfile,ignoredates)

	def _get_files(self,bucketpath,dirsource):
		#returns a list of tuples = >[(localFilePath,bucketPath), (localFilepath,bucketPath)]
		#this only reads files in the source directory and isn't recursive
		files = []
		dirsource = os.path.relpath(os.path.abspath(dirsource))
		for filename in os.listdir(dirsource):
			flpath = os.path.join(dirsource,filename)
			abspath = os.path.abspath(flpath)
			flpath = os.path.relpath(abspath)
			if os.path.isdir(flpath): continue
			bktflname = "%s%s" % (bucketpath,filename)
			bktflname = re.sub("//","/",bktflname)
			files.append((flpath,bktflname))
		return files
	
	def _get_files_recursive(self,bucketpath,dirsource):
		#returns a list of tuples = >[(localFilePath,bucketPath), (localFilepath,bucketPath)]
		#but this also recurses into directories.
		files = []
		dirsource = os.path.relpath(os.path.abspath(dirsource))
		for dirname, dirnames, filenames in os.walk(dirsource):
			for filename in filenames:
				localpath = os.path.join(dirname,filename)
				bucketlocal = re.sub("^"+dirsource,"",localpath)
				bucket = "%s%s" % (bucketpath,bucketlocal)
				bucket = re.sub("//","/",bucket)
				files.append((localpath,bucket))
		return files

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-a","--api",help="S3 API Key")
	parser.add_argument("-s","--secret",help="S3 Secret")
	parser.add_argument("-d","--source",help="Source directory")
	parser.add_argument("-f","--file",help="Source file to upload")
	parser.add_argument("-b","--bucket",help="S3 Bucket")
	parser.add_argument("-p","--bucketpath",help="S3 Bucket path. Use as a base path for directories. An absolute path for files.")
	parser.add_argument("-r","--recursive",action="store_true",help="Whether to recurse into local source directory")
	parser.add_argument("-i","--ignoredates",action="store_true",help="Ignore modified dates and upload all files")
	parser.add_argument("-t","--threads",default=1,type=int,help="The number of threads to use to upload files")
	args = parser.parse_args()
	uploader = S3Uploader(args.api,args.secret)
	if args.source:
		uploader.upload_dir(args.bucket,args.bucketpath,args.source,args.recursive,args.threads,args.ignoredates)
	elif args.file:
		uploader.upload_file(args.bucket,args.bucketpath,args.file,args.ignoredates)
	else:
		print "py-s3uploader -h"
