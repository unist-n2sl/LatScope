import ebpf_conf
import ebpf_preprocess

from time_sync_manage import ebpf_python
import ebpf_time_sync
import ebpf_mainprocess
import ebpf_analyzer
import ebpf_database

import time
from multiprocessing import Process
import threading as th

def periodic_time_sync(ec):
	time.sleep(ec.time_sync['time_interval'])
	
	while True:
		try:
			ept = ebpf_python.ebpfPython(ec)
			ets = ebpf_time_sync.ebpfTimesync(ec, ept)
			ets.__main__()
		except Exception as e:
			print(f'[time_sync] failed: {e}')

		time.sleep(ec.time_sync['time_interval'])

if __name__ == "__main__":
	ec = ebpf_conf.ebpfConf()
	ec.__main__()

	epp = ebpf_preprocess.ebpfPreprocess(ec)
	epp.__main__()

	ept = ebpf_python.ebpfPython(ec)
	ets = ebpf_time_sync.ebpfTimesync(ec, ept)
	ets.__main__()
	thread = th.Thread(target=periodic_time_sync, args=(ec,), daemon=True)
	thread.start()

	emp = ebpf_mainprocess.ebpfMainprocess(ec)
	emp.__main__()

	print("Analyzer start")
#	fid = int(input("flow id : "))
	fid = None

	ed = ebpf_database.ebpfDatabase(ec)
	ed.__connect__()
	ed.__delete__()
	ed.__create__()
	
	p = Process(target = ebpf_analyzer.ebpfAnalyzer, args = (ec, 0, fid, ))
	p.start()
	time.sleep(0.1)

	for i in range(1, 5):
		p = Process(target = ebpf_analyzer.ebpfAnalyzer, args = (ec, i, fid, ))
		p.start()

	# preprocess 객체를 빌린다.
	epp.rd.incr("analyzer_id")
	
	p.join()


