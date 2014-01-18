Upload a directory, optionally do recursive uploads, or upload a single file.

It also accepts a thread count to upload multiple files at once over a few S3Connections.

It requires boto from Amazon.

Options:

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