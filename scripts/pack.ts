import {readdir, stat, writeFile} from 'fs/promises'

import { exec } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const pExec = promisify(exec)

async function getAllFiles(dir: string) {
    if (dir.includes('moosyncLib')) {
        return []
    }

    const dirent = await readdir('python-src')
    const files: string[] = []
    for (const d of dirent) {
        const abs = path.join(dir, d)
        if ((await stat(abs)).isDirectory()) {
            files.push(...(await getAllFiles(abs)))
        }

        if (d.endsWith('.py') && !d.includes('setup.py') && !d.includes("main.py")) {
            files.push(abs)
        }   
    }

    return files
}

async function generateSetupPy() {
//     const dirent = (await getAllFiles('./python-src')).map(val => val.replace('python-src/', '').replace('.py', ''))
//     await writeFile(path.join('python-src', 'setup.py'), 
//     `from distutils.core import setup

// setup(
//     name='moosync-ext',
//     version='1.0',
//     packages=["moosyncLib"],
//     py_modules=["${dirent.join('", "')}"],
//     scripts=["main.py"],
// )
//     `)
}

async function generatePEX() {

    await generateSetupPy()
    await pExec('cd python-src && ../.venv/bin/pex . -r requirements.txt -c main.py -o ../python-bin.pex --disable-cache')
}

generatePEX()