import { mkdirSync, existsSync, readdirSync, lstatSync, writeFileSync, readFileSync } from 'node:fs';
import { exec, execSync } from 'node:child_process';
import * as path from 'node:path';

export const download = (tag: string, repo: string): string => {
    const cache_dir = path.resolve("cache", tag);
    mkdirSync(cache_dir, { recursive: true, });

    const kernel_dir = path.join(cache_dir, "linux");
    if (!existsSync(kernel_dir)) {
        execSync(`git clone --progress --depth 1 --branch ${tag} ${repo} ${kernel_dir}`, { stdio: "inherit", });
    }

    return kernel_dir;
};

/*
    Expects `cache` to point to the directory that the `linux` repo has been installed to.
*/
export const cache_headers = (cache: string, arches: string[]): string => {
    const header_dir = path.resolve(cache, "headers");
    mkdirSync(header_dir, { recursive: true });
    
    const kernel_dir = path.resolve(cache, "linux");

    for (const arch of arches) {
        const install_dir = path.join(header_dir, arch);
        if (!existsSync(install_dir)) {
            mkdirSync(install_dir, { recursive: true });
            try {
                execSync(`make headers_install ARCH=${arch} INSTALL_HDR_PATH=${install_dir}`, { cwd: kernel_dir, stdio: "inherit", });
            } catch {}
        }
    }

    return header_dir;
};

export const get_arch_paths = (kernel: string): string[] => {
    const arch = path.join(kernel, "arch");
    return readdirSync(arch)
        .map(file => path.join(arch, file))
        .filter(file => lstatSync(file).isDirectory());
};