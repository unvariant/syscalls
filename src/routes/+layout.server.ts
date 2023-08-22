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

const search = (victim: string, ok: { (file: any): boolean }): string[] => {
    return readdirSync(victim)
        .map(file => path.join(victim, file))
        .map(file => {
            const stat = lstatSync(file);
            if (stat.isDirectory()) {
                return search(file, ok);
            } else if (stat.isFile()) {
                return file;
            } else {
                return "";
            }
        })
        .flat()
        .filter(file => ok(file));
}

const parse_table = (file: string): Syscall[] => {
    return readFileSync(file)
        .toString()
        .trim()
        .split('\n')
        .filter(ln => ln.length != 0 && !ln.startsWith('#'))
        .map(ln => ln.split(/\s+/))
        .map(([nr, abi, name, entrypoint]) => {
            return {
                "nr": nr,
                "abi": abi,
                "name": name,
                "entrypoint": entrypoint,
            };
        });
}

export const load: LayoutServerLoad = async () => {
	const tag: string = "v6.5-rc6";
	const repo: string = "https://github.com/torvalds/linux";
    const kernel_dir = download(tag, repo);
    const cache_dir = path.dirname(kernel_dir);
    const arch_paths = get_arch_paths(kernel_dir);
    const arch_names = arch_paths.map(file => path.basename(file));
    const header_dir = cache_headers(cache_dir, arch_names);
    console.log("done");
	// if (!existsSync("kernel")) {
	// 	mkdirSync("kernel");
	// }
	// const local = path.join("kernel", tag);
	// if (!existsSync(local)) {
	// 	child_process.execSync(`git clone --progress --depth 1 --branch ${tag} ${repo} ${local}`, {
	// 		stdio: "inherit",
	// 	});
	// }
    // const cache_dir = path.join("kernel", "cache", tag);
    // if (!existsSync(cache_dir)) {
    //     mkdirSync(cache_dir, { recursive: true, });
    // }
    // const cache_file = path.join(cache_dir, "syscalls.json");
    // let all: Map<string, {path: string, line: string, args: { name: string, type: string, }[]}> = new Map();
    // if (!existsSync(cache_file)) {
    //     const output = child_process.execSync(
    //         `rg --multiline --multiline-dotall --json --type c '^SYSCALL_DEFINE.\\(\\w+,.*?\\)' .`,
    //         { cwd: local, } )
    //         .toString();
    //     output
    //         .trim()
    //         .split('\n')
    //         .map(raw => JSON.parse(raw))
    //         .filter(raw => raw.type == "match")
    //         .forEach(json => {
    //             const path = json.data.path.text;
    //             const line = json.data.line_number;
    //             let match = json.data.lines.text;
    //             match = match.slice(match.indexOf('(') + 1, match.indexOf(')'));
    //             const [name, ...rawargs] = match.split(',').map((arg: string) => arg.trim());
    //             const args = [];
    //             for (let i = 0; i < rawargs.length; i += 2) {
    //                 args.push({
    //                     "name": rawargs[i + 1],
    //                     "type": rawargs[i],
    //                 });
    //             }
    //             const entry = { "path": path, "line": line, "args": args, };
    //             all.set(`${name}-${path}`, entry);
    //         });
    //     writeFileSync(cache_file, JSON.stringify([...all.entries()]));
    // } else {
    //     all = new Map(JSON.parse(readFileSync(cache_file).toString()));
    // }
    // const arch_dir = path.join(local, "arch");
    // const archpaths =
    //     readdirSync(arch_dir)
    //     .map(file => path.join(arch_dir, file))
    //     .filter(file => lstatSync(file).isDirectory());
    // const tables = archpaths.map(file => {
    //     return {
    //         "arch": path.basename(file),
    //         "tables": search(file, (file) => path.basename(file).startsWith("syscall") && path.extname(file) == ".tbl"),
    //     };
    // });
    // const archs = tables.map(({ arch, tables, }) => {
    //     return {
    //         "arch": arch,
    //         "syscalls": tables.map(parse_table).flat(),
    //     };
    // });
    return {};
	// return {
	// 	"all": all,
    //     "archs": archs,
	// };
};
