import { mkdirSync, readdirSync, lstatSync, existsSync, writeFileSync, readFileSync } from 'node:fs';
import * as path from 'node:path';
import * as child_process from 'node:child_process';
import { download, cache_headers, get_arch_paths } from './syscalls';

import type { LayoutServerLoad } from './$types';

export const prerender = true;

/*

Handle parsing the syscall tables and generic syscalls.
See: https://www.kernel.org/doc/html/latest/process/adding-syscalls.html#adding-a-new-system-call.

Architectures that define their own syscall numbers will have a corresponding syscall*.tbl defining
those numbers. Otherwise they use the syscall numbers defined in include/uapi/asm-generic/unistd.h.

The architecture specific syscalls are found by searching for SYSCALL_DEFINE[n].
The generic syscalls are found by parsing include/uapi/asm-generic/unistd.h and looking for __SYSCALL
as well as #define __NR.

*/

export interface Syscall {
    nr: string,
    abi: string,
    name: string,
    entrypoint: string,
};

export const load: LayoutServerLoad = async () => {
    return {};
};
