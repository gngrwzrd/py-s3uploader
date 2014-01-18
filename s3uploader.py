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
	
	def __init__(self,api,secret):
		self.api = api
		self.secret = secret
	
	def upload_dir(self,bucket,bucketbasepath,dirsource,recursive,threadcount,ignoredates):
		files = []
		if recursive: files = self._get_files_recursive(bucketbasepath,dirsource)
		else: files = self._get_files(bucketbasepath,dirsource)
		if(threadcount > 1):
			c = math.ceil(float(len(files))/threadcount)
			threads = []
			thread_pairs = []
			for i in range(int(c)):
				thread_pairs.append([])
				for j in range(threadcount):
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
			print "%s => %s" % (localfile,bucketfile)
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
	s3sync = S3Uploader(args.api,args.secret)
	if args.source:
		s3sync.upload_dir(args.bucket,args.bucketpath,args.source,args.recursive,args.threads,args.ignoredates)
	elif args.file:
		s3sync.upload_file(args.bucket,args.bucketpath,args.file,args.ignoredates)
