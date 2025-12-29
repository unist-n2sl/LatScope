# LatScope: End-to-End Latency Decomposition Across the Cloud Network Stack

## Intro
* In large-scale cloud and virtualized systems, improving performance requires understanding not just total latency, but where delays actually occur across the network stack.
* Latency can emerge at multiple layers---including socket, TCP, IP, device, and virtual interfaces---and these delays often change depending on workload behavior, network conditions, and system configuration.
* Existing tools mainly measure RTT or single-layer metrics, making it difficult to perform real-time, practical, cross-layer latency analysis in complex environments.
* LatScope fills this gap by using eBPF to match packets across layers and compute accurate inter-layer delays, while XDP-based time synchronization enables precise inter-server latency breakdowns.
* With low-overhead, fine-grained latency decomposition, LatScope helps engineers detect bottlenecks, troubleshoot anomalies, and make informed tuning decisions in real deployments.

## Background
* This project leverages eBPF and XDP to enable fast, low-overhead network performance monitoring in large-scale systems.
* eBPF (extended Berkely Packet Filter) 
    * A kernel technology that allows user-defined programs to run safely inside restricted parts of the operating system without modifying kernel code.
    * It provides rich visibility into networking, system, and application events while maintaining high performance, making it suitable even for 10-Gbps-class per-core environments.
* XDP (eXpress Data Path)
    * A high-performance, eBPF-based packet processing framework that runs at the earliest point in the network stack, enabling packets to be handled or redirected before entering the kernel networking path.
    * It can process traffic at multi-million packets-per-second (Mpps) rates, making it ideal for real-time latency observation and lightweight data collection.

## Architecture
![Architecture](./img/latscope_architecture.pdf)

## Requirements
* Redis
	* For Communication Tool between other servers
* MySQL
	* For a storage as the data collected by Observer
* paramiko
	* Python Package which is used for SSH connection
	
## Code Structure
* Metric\_Collector
	* ebpf\_program\_vm
		* metric\_measure\_vm
			* ebpf\_code.py
			* ebpf\_conf.py
			* ebpf\_database.py
			* ebpf\_main.py
			* ebpf\_python.py
		* time\_sync
			* ebpf\_code.py
			* ebpf\_conf.py
			* ebpf\_main.py
			* ebpf\_python.py
	* time\_sync\_manage
		* ebpf\_code.py
		* ebpf\_python.py
	* ebpf\_preprocess.py
	* ebpf\_terminal.py
	* ebpf\_database.py
	* ebpf\_conf.py
	* ebpf\_analyzer.py
	* ebpf\_main.py
	* conf
		* connect\_info.yaml
		* function\_info.yaml
		* ping\_info.yaml
		* sampling\_info.yaml
		* database\_info.yaml
		* management\_server\_info.yaml
		* redis\_info.yaml

## Code File
* time\_sync\_manage
	* It is used by Management server for Time Synchronization between each servers
	* It make UDP packet and send them to other servers
* time\_sync
	* It is used by Observer for Time Synchronization
	* It installed XDP program
* ebpf\_program\_vm
	* Observer Code
	* It collects network metric to central database
* ebpf\_analyzer
	* It calculates the network performance
* ebpf\_preprocess
	* It install Observer code in each server
	* It set tables in Relational Database
* ebpf\_mainprocess
	* It executes Observer in each server
* ebpf\_main
	* It is a entry point

## Configuration FILE
* conf
	* connect\_info.yaml (server connect info (address, port, virtual machine etc..))
	    
		| variable | meaning | example |
		| -------- | ------- | ------- |
		| address  | address (used by ssh) | 10.1.1.1 |
		| port     | port (used by ssh) | 5000 |
		| username | name (used by ssh) | sonic |
		| hostname | server name (used by analyzer) | node1 |
		| metadata_key | unique key (used by per server) | 1 |
		| novm | it is a bare-metaal server | metadata_key |
		| isvm | who is the vm's host | metadata_key |
		| eth | which interface attach | interface names |
		| other_address | other address (used by server) | other address |
		| iscontainer | who is the container's host | metadata_key |
	* function\_info.yaml (Which function probed? Not Yet Activated)
	* ping\_info.yaml (Information for Time-Synchronization)
		
		| variable | meaning | example |
		| -------- | ------- | ------- |
		| address | address (where to ping) | 10.1.1.1 |
		| port | port (where to ping) | 5000 |
		| eth | interface (used by XDP) | enp1s0 |
	* sampling\_info.yaml (Information for Sampling Rate, Address, Port)

		| variable | meaning | example |
		| -------- | ------- | ------- |
		| size | sampling rate (payload size) | 72400 (bytes) |
		| interval | sampling rate (time interval) | 1 (sec) |
		| ports | sampling port (port that interested) | 5000 |
	* database\_info.yaml (Information for Database (Address, Port, Passwd etc..))

		| variable | meaning | example |
		| -------- | ------- | ------- |
		| user | db's user | xxxx |
		| passwd | db's password | xxxx |
		| host | db's address | xxxx |
		| db | which db | xxxx |
	* management\_server\_info.yaml (Information for Management server (Reporting, Communication etc..))
		
		| variable | meaning | example |
		| -------- | ------- | ------- |
		| address | manager server's address | 10.1.1.1 |
		| port | manager server's port | 5000 |
		| username | manager server's name | xxxx |
		| password | manager server's password | xxxx |
		| hostname | manager server's hostname | xxxx |
		| eth | manager server's interface (used by XDP) | xxxx |
	* redis\_info.yaml (Information for KV Store (Address, Port, Passwd etc..))

		| variable | meaning | example |
		| -------- | ------- | ------- |
		| address | redis's address | 10.1.1.1 |
		| port | redis's port | 5000 |

## Example
* Result Example
	* Result Example1 (LAN)
		* ![Result Example1 (LAN)](./img/lan.png)
	* Result Example2 (LTE)
		* ![Result Example2 (LTE)](./img/lte.png)
	* Result Example3 (WIFI)
		* ![Result Example3 (WIFI)](./img/wifi.png)
