import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async ({ parent, params, }) => {
    const data = await parent();
    const syscalls = data.archs.filter(({ arch }) => arch == params.arch)[0].syscalls;
    return {
        "syscalls": syscalls,
    };
};