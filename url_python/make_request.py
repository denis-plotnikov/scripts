#!/usr/bin/python
import urllib2
import urllib
import time
import sys
import math
import re
from cookielib import CookieJar
from multiprocessing.pool import ThreadPool
from threading import Lock


PCNT_UPPER_BOUND = 10000 # msec
PCNT_RANGE = 100
PERCENTILE = [0 for i in range(0, PCNT_RANGE + 1)]
PCNT_LOCK = Lock()
REQ_LOCK = Lock()
ERR_LOCK = Lock()
MAX_RESP_LOCK = Lock()
RES_DICT = {
		"requests": 0,
		"errors": 0,
		"max_response": 0.0
}

class ContentError(Exception):
	pass

def pcnt_reg_val(val):
	index = int(round(val * 1000 * PCNT_RANGE / PCNT_UPPER_BOUND))
	index = min(index, PCNT_RANGE)
	PCNT_LOCK.acquire()
	PERCENTILE[index] += 1
	PCNT_LOCK.release()

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

def reg_req():
	REQ_LOCK.acquire()
	RES_DICT["requests"] = RES_DICT["requests"] + 1
	REQ_LOCK.release()

def reg_error():
	ERR_LOCK.acquire()
	RES_DICT["errors"] = RES_DICT["errors"] + 1
	ERR_LOCK.release()

def reg_max_response(val):
	MAX_RESP_LOCK.acquire()
	RES_DICT["max_response"] = max(RES_DICT["max_response"], val)
	MAX_RESP_LOCK.release()

def default_page_load(ip_addr):
	opener = urllib2.build_opener()
	url = "http://{0}/test.html".format(ip_addr)
	response = opener.open(url, None)
	content = response.read()
	return content

def check_stub(content):
	pass

def default_load_routine(args):
	host = args[0]
	run_time = args[1]
	rate = args[2]
	load_routine_core(host, run_time, rate, default_page_load, check_stub)

def plesk_visit_mainpage(ip_addr):
	cj = CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	formdata = {
		"success_redirect_url":"",
		"login_name":"root",
		"passwd":"",
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

def load_routine_core(ip_addr, run_time, rate, request_func, check_func):
	if rate:
		delay = 1.0 / rate
	else:
		delay = 0.0

	etime = time.time() + run_time
	while time.time() < etime:
		reg_req()
		stime = time.time()
		try:
			(t, content) = timing(request_func, ip_addr)
			check_func(content)
		except urllib2.URLError as e:
			reg_error()
		except ContentError:
			reg_error()
		else:
			pcnt_reg_val(t)
			reg_max_response(t)
		dtime = time.time() - stime
		wait_time = delay - dtime
		if(wait_time > 0):
			time.sleep(wait_time)

def plesk_load_routine(args):
	host = args[0]
	run_time = args[1]
	rate = args[2]
	load_routine_core(p_addr, run_time, rate, plesk_visit_mainpage, plesk_check_content)

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

def main(host, thread_num, run_time, rate = 0.0):
	#plesk_load_routine(ip_addr, run_time, rate = 0.0)
	#load_nums = [i for i in range(5)]
	#multiload_routine(load_nums, uniform_max_load_distr, dummy_load_routine, run_time, rate)
#	hosts = ['10.30.118.130', '10.30.118.131']
#	multiload_routine(hosts, uniform_max_load_distr, plesk_load_routine, run_time, rate)

	hosts = [host for i in range(thread_num)]
	multiload_routine(hosts, uniform_max_load_distr, default_load_routine, run_time, rate)

	percentile = 90
	print(
		"Requests: {0}\n"
		"Errors: {1}\n"
		"Percentile {2}: {3} ms\n"
		"Max response time: {4} ms\n"
		.format(
			RES_DICT["requests"],
			RES_DICT["errors"],
			percentile, pcnt_get(percentile),
			int(RES_DICT["max_response"] * 1000)
		)
	)

if __name__ == "__main__":
	args_num = len(sys.argv) 
	thread_num = 1
	run_time = 10
	rate = 0.0

	host = sys.argv[1]
	if args_num > 2:
		thread_num = int(sys.argv[2])
	if args_num > 3:
		run_time = float(sys.argv[3])
	if args_num > 4:
		rate = float(sys.argv[4])

	main(host, thread_num, run_time, rate)
