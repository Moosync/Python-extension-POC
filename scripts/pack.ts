import { readFile, readdir, stat, writeFile } from 'fs/promises'

import { exec } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const pExec = promisify(exec)

async function getAllFiles(dir: string) {
    if (dir.includes('moosyncLib')) {
        return []
    }

    const dirent = await readdir(dir)
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
    const dirent = (await getAllFiles('./python-src')).map(val => val.replace('python-src/', '').replace('.py', ''))
    const requirements = (await readFile(path.join('python-src', 'requirements.txt'), { encoding: 'utf-8' })).split('\n')

    await writeFile(path.join('python-src', 'setup.py'),
        `from distutils.core import setup

setup(
    name='moosync-ext',
    version='1.0',
    packages=["moosyncLib"],
    py_modules=["${dirent.join('", "')}"],
    scripts=["main.py"],
    install_requires=["${requirements.join('", "')}"]
)
`)
}

async function generatePlatforms() {
    const version = (await pExec(`.venv/bin/python --version`)).stdout
    if (!version) {
        console.error("Failed to get python versions")
        process.exit(1)
    }

    const majorV = version.replace('Python ', '').trim().split('.').splice(0, 2).join('.')
    const abi = majorV.split('.').join('')
    return `--platform musllinux_1_1-x86_64-cp-${majorV}-cp${abi} --platform manylinux_2_17-x86_64-cp-${majorV}-cp${abi} --platform win32-cp-${majorV}-cp${abi} --platform macosx_11_0_x86_64-cp-${majorV}-cp${abi}`
}

async function generatePEX() {
    await generateSetupPy()
    await pExec(`cd python-src && ../.venv/bin/pex . -r requirements.txt -c main.py -o ../python-bin.pex --disable-cache ${await generatePlatforms()}`)
}

generatePEX()