Upload a directory, optionally do recursive uploads, or upload a single file.

It also accepts a thread count when uploading a directory for multiple files at once.

It requires boto from Amazon:

    sudo easy_install boto

Command Options:
 
("-a","--api",help="S3 API Key")    
("-s","--secret",help="S3 Secret")    
("-d","--source",help="Source directory")    
("-f","--file",help="Source file to upload")    
("-b","--bucket",help="S3 Bucket")    
("-p","--bucketpath",help="S3 Bucket path. Use as a base path for directories. An absolute path for files.")    
("-r","--recursive",action="store_true",help="Whether to recurse into local source directory")    
("-i","--ignoredates",action="store_true",help="Ignore modified dates and upload all files")    
("-t","--threads",default=1,type=int,help="The number of threads to use to upload files")    

Command Usage Examples:

Recursively upload files from local/folder/ to S3 mybucket/s3/folder/    
    ./py-s3uploader -a "MYAPI" -s "SECRET" -d "local/folder/" -b "mybucket" -p "s3/folder/" -i -r -t 3

Recursively upload newer files from local/folder/ to S3 mybucket/s3/folder/    
    ./py-s3uploader -a "MYAPI" -s "SECRET" -d "local/folder/" -b "mybucket" -p "s3/folder/" -r -t 3

Upload a single file:    
    ./py-s3uploader -a "MYAPI" -s "SECRET" -f "local/file.txt" -b "mybucket" -p "s3/folder/file.txt"

Class Usage Example:

    import s3uploader
    uploader = S3Uploader(args.api,args.secret)
	if args.source:
		uploader.upload_dir(args.bucket,args.bucketpath,args.source,args.recursive,args.threads,args.ignoredates)
	elif args.file:
		uploader.upload_file(args.bucket,args.bucketpath,args.file,args.ignoredates)

