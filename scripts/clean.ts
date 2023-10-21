import { rm } from 'fs/promises'

async function removePEX() {
    await rm('./python-bin.pex', { force: true })
}

removePEX()