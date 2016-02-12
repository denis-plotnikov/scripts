#!/usr/bin/python
import re, subprocess, copy, os


class NetAdapter():
	def __init__(self, name, ip, net_names):
		self.name = name
		self.ip = ip
		self._net_names = set()
		self.add_net_names(net_names)

	def add_net_names(self, names):
		# names is a list
		self._net_names.update(names)

	def get_net_names(self):
		# returns string
		return self._net_names

	def __hash__(self):
		return hash(self.name)


class Host():
	def __init__(self, role):
		self._net_adapters = set()
		self._ctid = None
		self.role = role

	def add_adapter(self, net_adapter):
		adapter = copy.deepcopy(net_adapter)
		self._net_adapters.add(adapter)

	def get_adapters(self):
		return copy.deepcopy(self._net_adapters)

	def get_ctid(self):
		return self._ctid

	def set_ctid(self, ctid):
		if self._ctid:
			raise Exception("Host has already got its ctid")
		else:
			self._ctid = ctid


def exe(command):
	p = subprocess.Popen(command,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE)
	out, _ = p.communicate()
	return out

def _assign_ctids(hosts, source):
	print (source)
	lines = source.split("\n")
	for line in lines[1:]: # omit headers - line #0
		name_search = re.search("vcons_.+_[0-9]+", line)
		if not name_search:
			continue
		host_name = name_search.group(0)
		num_search = re.search("_[0-9]+$", host_name)
		num = num_search.group(0)
		order_digits_len = len(num)
		host_name = host_name[len("vcons_"):-order_digits_len]
		ctid_search = re.search("^\s+[0-9]+\s+", line)
		ctid = ctid_search.group(0)
		ctid = ctid.strip()
		try:
			hosts[host_name].set_ctid(ctid)
		except KeyError:
			continue


def _set_host_adapters(host):
	for net_adapter in host.get_adapters():
		cmd = "prlctl set {0} --netif_add {1}"\
				.format(host.get_ctid(), net_adapter.name)
		res = exe(cmd.split(" "))
		print(res)
		print("{0}:{1}-->{2}".format(host.get_ctid(), net_adapter.name, net_adapter.ip))
		#print(res)

		cmd = "prlctl set {0} --ifname {1} --ipadd {2}/16 --network Bridged"\
				.format(host.get_ctid(), net_adapter.name, net_adapter.ip)
		res = exe(cmd.split(" "))
		print(res)

def _start_host(host):
	cmd = "vzctl start {0}".format(host.get_ctid())
	ret = exe(cmd.split(" "))
	print (ret)

def _stop_host(host):
	cmd = "vzctl stop {0}".format(host.get_ctid())
	ret = exe(cmd.split(" "))
	print (ret)

def _clear_known_hosts(ctid):
	cmd = "vzctl exec {0} \"> /etc/hosts\"".format(ctid)
	os.system(cmd)

def _add_host_info(ctid, entry_ip, entry_names):
	# entry_names is a list
	cmd = "vzctl exec {0} \"echo {1} {2} >> /etc/hosts\""\
			.format(ctid, entry_ip, " ".join(entry_names))
	os.system(cmd)

def _setup_hostnames(cur_host, host_list):
	ctid = cur_host.get_ctid()
	_clear_known_hosts(ctid)
	_add_host_info(ctid, "127.0.0.1", ["localhost.localdomain", "localhost"])
	_add_host_info(ctid, "::1", ["localhost", "localhost.localdomain",\
					"localhost6", "localhost6.localdomain6"])

	for host in host_list.itervalues():
		for adapter in host.get_adapters():
			_add_host_info(ctid, adapter.ip, adapter.get_net_names())

def _remove_all_netif(host):
	for adapter in host.get_adapters():
		cmd = "prlctl set {0} --netif_del {1}"\
			.format(host.get_ctid(), adapter.name)
		os.system(cmd)
def main():
	print ("Assigning IPs...")

	hosts = {
		"application_server":Host("application_server"),
		"batch_server":Host("batch_server"),
		"database_server":Host("databse_server"),
		"infrastructure_server":Host("infrastructure_server"),
		"mail_server":Host("mail_server"),
		"web_server":Host("web_server"),
		"test_client":Host("test_client"),
	}

	# external communication network (VM-to-client)
	ex_eth = "eth0"
	hosts["application_server"].add_adapter(
		NetAdapter(ex_eth, "10.30.118.145", ["appserver", "appserver1",
						"specdelivery", "specemulator"]))
	hosts["batch_server"].add_adapter(
		NetAdapter(ex_eth, "10.30.118.146", ["batchserver", "batchserver1"]))
	hosts["database_server"].add_adapter(
		NetAdapter(ex_eth, "10.30.118.147", ["dbserver", "dbserver1"]))
	hosts["infrastructure_server"].add_adapter(
		NetAdapter(ex_eth, "10.30.118.148", ["infraserver", "infraserver1"]))
	hosts["mail_server"].add_adapter(
		NetAdapter(ex_eth, "10.30.118.149", ["mailserver", "mailserver1"]))
	hosts["web_server"].add_adapter(
		NetAdapter(ex_eth, "10.30.118.150", ["webserver", "webserver1"]))
	hosts["test_client"].add_adapter(
		NetAdapter(ex_eth, "10.30.118.151", ["client1", "specdriver"]))

	# internal communication network (VM-to-VM)
	in_eth = "eth1"
	hosts["application_server"].add_adapter(
		NetAdapter(in_eth, "10.28.68.145", ["appserver1-int"]))
	hosts["database_server"].add_adapter(
		NetAdapter(in_eth, "10.28.68.147", ["dbserver1-int", "specdb"]))
	hosts["infrastructure_server"].add_adapter(
		NetAdapter(in_eth, "10.28.68.148", ["infraserver1-int"]))
	hosts["web_server"].add_adapter(
		NetAdapter(in_eth, "10.28.68.150", ["webserver1-int"]))

	ctid_source = exe(["vzlist", "-a", "-n"])
	_assign_ctids(hosts, ctid_source)

	for host in hosts.itervalues():
		print("{0}:{1}".format(host.role, host.get_ctid()))

	active_hosts = [x for x in hosts.itervalues() if x.get_ctid()]
	print ("Removing old net settings ...")
	map(_remove_all_netif, active_hosts)
	print("Applying new net settings ...")
	map(_set_host_adapters, active_hosts)
	print("Starting hosts ...")
	map(_start_host, active_hosts)

	print("Setting host names ...")
	for current_host in active_hosts:
		_setup_hostnames(current_host, hosts)


if __name__ == "__main__":
	main()
