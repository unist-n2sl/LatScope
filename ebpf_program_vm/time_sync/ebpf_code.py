class ebpfCode:
	def __init__(self):
		self.function_name = ["syncTimeProtocol"]
	
	def __set_header__(self):
		return '''
			#include <uapi/linux/bpf.h>	
			#include <linux/if_ether.h>
			#include <linux/ip.h>
			#include <linux/tcp.h>
			#include <linux/udp.h>
			#include <linux/in.h>

			#define PING_PORT ( (u16) 5999 )
		'''
	
	def __set_map__(self):
		return '''
			BPF_PERF_OUTPUT(xdp_events);
			BPF_TABLE("hash", u8, u32, t_addr, 1);
		'''

	def __set_common_func__(self):
		return '''
			static u16 calc_ip_checksum(struct iphdr *iphdr) {
				u32 sum = 0;
				u16 checksum = 0;
				u16 data[10];
				s16 i;

				bpf_probe_read_kernel(data, sizeof(data), iphdr);
				for (i = 0; i < 10; i++) sum += data[i];
				checksum += sum;
				checksum += (sum >> 16);
				checksum += (sum >> 16);
				checksum = ~checksum;
				return checksum;
			}
            static __always_inline __u16 csum_fold_helper(__u64 csum) {
                int i;
                for (i = 0; i < 4; i++)
                {
                    if (csum >> 16)
                        csum = (csum & 0xffff) + (csum >> 16);
                }
                return ~csum;
            }

            static __always_inline __u16 iph_csum(struct iphdr *iph) {
                iph->check = 0;
                unsigned long long csum = bpf_csum_diff(0, 0, (unsigned int *)iph, sizeof(struct iphdr), 0);
                return csum_fold_helper(csum);
            }
            static __attribute__((__always_inline__)) static inline void ipv4_l4_csum(void *data_start, __u32 data_size, __u64 *csum, struct iphdr *iph) {
                __u32 tmp = 0;
                *csum = bpf_csum_diff(0, 0, &iph->saddr, sizeof(__be32), *csum);
                *csum = bpf_csum_diff(0, 0, &iph->daddr, sizeof(__be32), *csum);
                tmp = __builtin_bswap32((__u32)(iph->protocol));
                *csum = bpf_csum_diff(0, 0, &tmp, sizeof(__u32), *csum);
                tmp = __builtin_bswap32((__u32)(data_size));
                *csum = bpf_csum_diff(0, 0, &tmp, sizeof(__u32), *csum);
                *csum = bpf_csum_diff(0, 0, data_start, data_size, *csum);
                *csum = csum_fold_helper(*csum);
            }
            static void
            ipv4_l4_csum_inline(void *data_end, void *l4_hdr, struct iphdr *iph, unsigned long *csum)
            {
            	unsigned int ip_addr;
            	unsigned short *next_iph_u16;
            	unsigned char *last_byte;
            	/* Psuedo header */
            	ip_addr = ntohl(iph->saddr);
            	*csum += (ip_addr >> 16) + (ip_addr & 0xffff);
            	ip_addr = ntohl(iph->daddr);
            	*csum += (ip_addr >> 16) + (ip_addr & 0xffff);
            	*csum += (unsigned short)iph->protocol;
            	*csum += (unsigned short)((long)data_end - (long)l4_hdr);
            	next_iph_u16 = (unsigned short *)l4_hdr;
            	const unsigned short length = (unsigned long long)data_end - (unsigned long long)next_iph_u16;
            	const unsigned short nr = length / 2;
            	for (int i = 0; i < nr; i++) {
            		*csum += ntohs(*next_iph_u16);
            		next_iph_u16++;
            	}
            	/* printf("len: %d, %d\n", length, nr); */
            	if ((void *)next_iph_u16 < data_end) {
            		last_byte = (unsigned char *)next_iph_u16;
            		if ((void *)(last_byte + 1) <= data_end) {
            			*csum += ((unsigned short)(*last_byte)) << 8;
            		}
            	}
            	*csum = csum_fold_helper(*csum);
            }
			static void swap_packet(struct iphdr **iphdr, struct ethhdr **eth) {
				u32 taddr;
				unsigned char t_macaddr;
				s16 i;

				taddr = (*iphdr)->saddr;
				(*iphdr)->saddr = (*iphdr)->daddr;
				(*iphdr)->daddr = taddr;

				for (i = 0; i < ETH_ALEN; i++) {
					t_macaddr = (*eth)->h_source[i];
					(*eth)->h_source[i] = (*eth)->h_dest[i];
					(*eth)->h_dest[i] = t_macaddr;
				}
				return;
			}

			static void fill_data(struct iphdr **iphdr, struct udphdr **udphdr, void* data_end) {
				u64 ts = bpf_ktime_get_boot_ns();
                u8* valp = 0;
                if( (u8*) ((*udphdr)+1) + 8 > data_end )
                    return;
                memcpy((void*)((*udphdr)+1), &ts, sizeof(ts));

                /*
				(*udphdr)->len = (*udphdr)->dest;
				(*iphdr)->id = (*iphdr)->frag_off = 0;
				(*udphdr)->source = (*udphdr)->dest = 0;
				(*iphdr)->id |= (ts >> 48);
				(*iphdr)->frag_off |= (ts >> 32);
				(*udphdr)->source |= (ts >> 16);
				(*udphdr)->dest |= ts;
                */
			}

			static u32 get_host(void) {
				u8 key = 1;
				u32 *addr;

				addr = t_addr.lookup(&key);
				if (addr) return *addr;
				return 0;
			}
		'''

	def __set_main_func__(self):
		return r'''
			int syncTimeProtocol(struct xdp_md *ctx) {
				void *data_begin = (void *)(long) ctx->data;
                void *data_end = (void *)(long) ctx->data_end;
                struct ethhdr *eth;
                struct iphdr *iphdr;
                struct udphdr *udphdr;

				u32 addr;
				u16 port;

                unsigned long cs = 0;

				eth = data_begin;
                if ((void *)(eth + 1) > data_end) return XDP_PASS;
                if (eth->h_proto != bpf_htons(ETH_P_IP)) return XDP_PASS;

                iphdr = (struct iphdr *) (((void *) eth) + ETH_HLEN);
                if ((void *)(iphdr + 1) > data_end) return XDP_PASS;
                if (iphdr->protocol != IPPROTO_UDP) return XDP_PASS;

                udphdr = (struct udphdr *)(iphdr + 1);
                if ((void *)(udphdr + 1) > data_end) {
					return XDP_PASS;
				}

				addr = iphdr->daddr;
				port = bpf_ntohs(udphdr->source);

				if (addr == get_host() && port == PING_PORT) {
					swap_packet(&iphdr, &eth);
                    u16 tport = udphdr->source;
                    udphdr->source = udphdr->dest;
                    udphdr->dest = tport;
					iphdr->check = iph_csum(iphdr);
                    udphdr->check = 0;
                    //ipv4_l4_csum_inline(data_end, udphdr, iphdr, cs);
                    //udphdr->check = cs;
					fill_data(&iphdr, &udphdr, data_end);
					return XDP_TX;
				}
				return XDP_PASS;
			}
		'''

	def __main__(self):
		code = self.__set_header__()
		code += self.__set_map__()
		code += self.__set_common_func__()
		code += self.__set_main_func__()

		return code
















