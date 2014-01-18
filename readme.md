Upload a directory, optionally do recursive uploads, or upload a single file.

It also accepts a thread count to upload multiple files at once over a few S3Connections.

It requires boto from Amazon.

Options:
 
("-a","--api",help="S3 API Key")    
("-s","--secret",help="S3 Secret")    
("-d","--source",help="Source directory")    
("-f","--file",help="Source file to upload")    
("-b","--bucket",help="S3 Bucket")    
("-p","--bucketpath",help="S3 Bucket path. Use as a base path for directories. An absolute path for files.")    
("-r","--recursive",action="store_true",help="Whether to recurse into local source directory")    
("-i","--ignoredates",action="store_true",help="Ignore modified dates and upload all files")    
("-t","--threads",default=1,type=int,help="The number of threads to use to upload files")    

Class Usage Example

    import s3uploader
    s3sync = S3Uploader(args.api,args.secret)
	if args.source:
		s3sync.upload_dir(args.bucket,args.bucketpath,args.source,args.recursive,args.threads,args.ignoredates)
	elif args.file:
		s3sync.upload_file(args.bucket,args.bucketpath,args.file,args.ignoredates)

