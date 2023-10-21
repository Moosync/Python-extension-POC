import { exec } from 'child_process';
import { promisify } from 'util';

const pExec = promisify(exec)

async function generatePEX() {
    await pExec('cd python-src && ../.venv/bin/pex . -r requirements.txt -c main.py -o ../python-bin.pex --disable-cache')
}

generatePEX()