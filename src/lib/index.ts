export interface Arg {
	fulltype: string;
	search: string;
	name: string;
}
export interface Syscall {
	nr: number;
	name: string;
	args: Arg[];
    path: string;
    line: number;
}
