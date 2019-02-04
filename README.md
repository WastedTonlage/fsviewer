# fsviewer
fsviewer is a utility that allows you to graphically see how you filesystem (only FAT16 and NTFS is supported) allocates disk space to files on your disk.

## Requirements

Requires Python 3.7 and PyQt5.

## Usage instruction

Run the utility with the following command:  
`python app.py <file system> <disk>`  
  
Example:  
`python app.py FAT C`  
  
Press `F5` to reload viewer after changing files on disk
