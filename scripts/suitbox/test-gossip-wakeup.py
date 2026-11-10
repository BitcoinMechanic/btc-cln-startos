#!/usr/bin/env python3
"""Compile the real gossip handler with I/O boundary spies; no daemon/funds needed."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);args=p.parse_args()
s=args.source.read_text();start=s.index('static void handle_gossip_in(');end=s.index('\nstatic void handle_gossip_timestamp_filter_in',start)
handler=s[start:end]
stubs=r'''
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
typedef unsigned char u8;
struct daemon {void *gossipd;};
struct peer {int id; struct daemon *daemon; void *peer_outq;};
static bool oversized;
static unsigned queue_length, wakes, forwards;
static void io_wake(void *p) { (void)p; wakes++; }
static unsigned daemon_conn_queue_length(void *p) { (void)p; return queue_length; }
static bool is_oversized_gossip_msg(const u8 *m) { (void)m; return oversized; }
#define status_peer_debug(...) ((void)0)
static u8 *towire_gossipd_recv_gossip(void *ctx,const int *id,const u8 *msg) { (void)ctx;(void)id;return (u8*)msg; }
static void log_peer_io(const struct peer *p,const u8 *msg) { (void)msg;io_wake(p->peer_outq); }
static void daemon_conn_send(void *p,u8 *msg) { (void)p;(void)msg;forwards++; }
#define take(x) (x)
'''
main=r'''
int main(void) {
 struct daemon d={0};struct peer p={.daemon=&d};u8 msg[1]={0};
 for(unsigned scenario=0;scenario<3;scenario++) {
  oversized=scenario==0;queue_length=scenario==1?500001:0;wakes=forwards=0;
  handle_gossip_in(&p,msg);
  if(!wakes) {fprintf(stderr,"FAIL: dropped gossip leaves reader asleep (scenario %u)\n",scenario);return 1;}
  if(forwards!=(scenario==2?1:0)) return 2;
 }
 puts("PASS: oversized, queue-full and forwarded gossip all resume peer I/O; dropped messages stay dropped");return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
 source=Path(tmp)/'test.c';binary=Path(tmp)/'test';source.write_text(stubs+handler+main)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
