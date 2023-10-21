import {access} from 'fs/promises'
import commandExists from 'command-exists'
import { exec } from 'child_process';
import { promisify } from 'util';

const pExec = promisify(exec)

async function checkPython() {
  const exists = await commandExists('python')
  return !!exists
}

async function checkVenv() {
  try {
    await access('./venv/bin/python')
    return true
  } catch {
    return false
  }
}

async function checkStuff() {
  if (!await checkVenv()) {
    if (await checkPython()) {
      await pExec('python -m venv ./.venv')
      return
    }

    throw new Error("Python not installed")
  }
}

async function installRequirements() {
  await pExec('./.venv/bin/pip install pex')
}

checkStuff().then(installRequirements)
