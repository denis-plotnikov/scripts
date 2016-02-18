#!/usr/bin/python
import urllib2
import urllib
import time
import sys
import math
import re
from cookielib import CookieJar


PCNT_UPPER_BOUND = 10000 # msec
PCNT_RANGE = 100
PERCENTILE = [0 for i in range(0, PCNT_RANGE + 1)]

class ContentError(Exception):
	pass

def pcnt_reg_val(val):
	index = int(round(val * 1000 * PCNT_RANGE / PCNT_UPPER_BOUND))
	index = min(index, PCNT_RANGE)
	PERCENTILE[index] += 1

def pcnt_get(percentile):
	pcnt_sum = sum(PERCENTILE)
	pcnt_num = math.ceil(1.0 *pcnt_sum * (100 - percentile) / 100)

	num_sum = 0
	idx = PCNT_RANGE-1
	for i in range(100, -1, -1):
		num_sum += PERCENTILE[i]
		if num_sum >= pcnt_num:
			idx = i
			break
	return idx * PCNT_UPPER_BOUND / PCNT_RANGE
	

def plesk_visit_mainpage():
	cj = CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	formdata = {
		"success_redirect_url":"",
		"login_name":"root",
		"passwd":"",
		"locale_id":"default"
	}
	data_encoded = urllib.urlencode(formdata)
	response = opener.open("https://10.30.18.198:8443/login_up.php3", data_encoded)
	content = response.read()
	response = opener.open("https://10.30.18.198:8443/smb/", None)
	content = response.read()
	return content
#	print(response)
#	with open("result.html", "w") as f:
#		f.write(content)

def plesk_check_content(content):
	res = re.search("Logged in as", content)
	if not res:
		raise ContentError

def timing(f, *args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        elapsed_time = time2 - time1
	return (elapsed_time, ret)


def main(run_time, rate = 0.0):
	print("Run time: {0} sec".format(run_time))
	requests = 0
	errors = 0
	max_responce_time = 0
	if rate:
		delay = 1.0 / rate
	else:
		delay = 0.0

	etime = time.time() + run_time
	while time.time() < etime:
		stime = time.time()
		try:
			requests += 1
			(t, content) = timing(plesk_visit_mainpage)
			plesk_check_content(content)
		except urllib2.URLError as e:
			errors += 1
		except ContentError:
			errors += 1 
		else:
			pcnt_reg_val(t)
			max_responce_time = max(t, max_responce_time)
		dtime = time.time() - stime
		wait_time = delay - dtime
		if(wait_time > 0):
			time.sleep(wait_time)
	percentile = 90
	print(
		"Requests: {0}\n"
		"Errors: {1}\n"
		"Percentile {2}: {3} ms\n"
		"Max response time {4} ms\n"
		.format(
			requests,
			errors,
			percentile, pcnt_get(percentile),
			int(max_responce_time * 1000)
		)
	)

if __name__ == "__main__":
	args_num = len(sys.argv) 
	run_time = 10
	rate = 0.0
	
	if args_num > 1:
		run_time = int(sys.argv[1])
	if args_num > 2:
		rate = float(sys.argv[2])
	
	main(run_time, rate)
