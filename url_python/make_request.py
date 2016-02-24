#!/usr/bin/python
import urllib2
import urllib
import time
import sys
import math
import re
from cookielib import CookieJar
from multiprocessing.pool import ThreadPool


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

def plesk_visit_mainpage(ip_addr):
	cj = CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	formdata = {
		"success_redirect_url":"",
		"login_name":"root",
		"passwd":"1q2w3e",
		"locale_id":"default"
	}
	data_encoded = urllib.urlencode(formdata)
	base_url = "https://{0}:8443/".format(ip_addr)
	login_url = "{0}/login_up.php3".format(base_url)
	response = opener.open(login_url, data_encoded)
	content = response.read()
	main_page_url = "{0}/smb/".format(base_url)
	response = opener.open(main_page_url, None)
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

def plesk_load_routine(ip_addr, run_time, rate = 0.0):
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
			(t, content) = timing(plesk_visit_mainpage, ip_addr)
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
		"Max response time: {4} ms\n"
		.format(
			requests,
			errors,
			percentile, pcnt_get(percentile),
			int(max_responce_time * 1000)
		)
	)

def multiload_routine(host_list, load_distr_function, load_func, run_time, max_rate):
	# get a list of rates to be applied to a corresponding host
	host_num = len(host_list)
	rates = load_distr_function(host_num, max_rate)

	#list of tuples - list of parameters to be passed to load_func
	params_list = list()
	for i in range(host_num):
		params_list.append((host_list[i], run_time, rates[i]))
	print(params_list)
	tp = ThreadPool(host_num)
	tp.map(load_func, params_list)
	tp.close()
	tp.join()

def uniform_max_load_distr(num, max_val):
	return [max_val for i in range(num)]

def dummy_load_routine(args):
	my_num = args[0]
	run_time = args[1]
	my_rate = args[2]
	print(
		"[{0}]: I'll sleep for {1} seconds (rate = {2})\n".
		format(my_num, run_time, my_rate))
	time.sleep(run_time)
	print("[{0}]I've done my sleeping!\n".format(my_num))

def main(ip_addr, run_time, rate = 0.0):
	#plesk_load_routine(ip_addr, run_time, rate = 0.0)
	load_nums = [i for i in range(5)]
	multiload_routine(load_nums, uniform_max_load_distr, dummy_load_routine, run_time, rate)


if __name__ == "__main__":
	args_num = len(sys.argv) 
	run_time = 10
	rate = 0.0

	ip_addr = sys.argv[1]
	if args_num > 2:
		run_time = int(sys.argv[2])
	if args_num > 3:
		rate = float(sys.argv[3])

	main(ip_addr, run_time, rate)
