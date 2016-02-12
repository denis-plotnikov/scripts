#!/usr/bin/python
import sys
import os

vztlib_path = os.path.join(os.path.dirname(__file__), "vztlib", "lib")
sys.path.append(vztlib_path)
from vztests.export_perf_results import CustomUpload

def upload_file(filename, description):
	with open(filename, 'r') as f:
		data = f.read()
	
	if len(data) > 0:
		uploader = CustomUpload(data, filename, description)
		uploader.upload("perf.sw.ru")
		print("File uploaded: UUID[{0}]".format(uploader.uuid))
	else:
		print("Upload failed. Can't read file {0}".format(filename))


if __name__ == "__main__":
	upload_file(sys.argv[1], sys.argv[2])
