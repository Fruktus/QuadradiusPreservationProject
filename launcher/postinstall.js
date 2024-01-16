import fs from 'fs/promises'
import fsPlain from 'fs'
import tar from 'tar'
import path from 'path'
import unzip from 'unzip'
import download from 'download'
import { exec } from 'child_process'

const outputDirectory = 'extras'

const platform = process.platform
const arch = process.arch

const pythonPlatform = {
    'aix': 'unknown',
    'darwin': 'unknown',
    'freebsd': 'unknown',
    'linux': 'unknown-linux-gnu',
    'openbsd': 'unknown',
    'sunos': 'unknown',
    'win32': 'pc-windows-msvc-shared',
}[platform]
const pythonArch = {
    'arm': 'unknown',
    'arm64': 'aarch64',
    'ia32': 'x86',
    'loong64': 'unknown',
    'mips': 'unknown',
    'mipsel': 'unknown',
    'ppc': 'unknown',
    'ppc64': 'ppc64le',
    'riscv64': 'unknown',
    's390': 'unknown',
    's390x': 's390x',
    'x64': 'x86_64',
}[arch]
const rufflePlatform = {
    'aix': 'unknown',
    'darwin': 'unknown',
    'freebsd': 'unknown',
    'linux': 'linux',
    'openbsd': 'unknown',
    'sunos': 'unknown',
    'win32': 'windows',
}[platform]
const ruffleFormat = {
    'aix': 'unknown',
    'darwin': 'unknown',
    'freebsd': 'unknown',
    'linux': 'tar.gz',
    'openbsd': 'unknown',
    'sunos': 'unknown',
    'win32': 'zip',
}[platform]

const pythonDistribution = `cpython-3.12.0+20231002-${pythonArch}-${pythonPlatform}-install_only.tar.gz`
const pythonDistributionUrl = `https://github.com/indygreg/python-build-standalone/releases/download/20231002/${pythonDistribution}`

const gameSwfUrl = 'https://github.com/Fruktus/QuadradiusClassic/raw/1.0.0/classic_quadradius/quadradius_game.swf'
const lobbySwfUrl = 'https://github.com/Fruktus/QuadradiusClassic/raw/1.0.0/classic_quadradius/quadradius_lobby.swf'

const ruffleDistribution = `ruffle-nightly-2024_01_16-${rufflePlatform}-x86_64.${ruffleFormat}`
const ruffleUrl = `https://github.com/ruffle-rs/ruffle/releases/download/nightly-2024-01-16/${ruffleDistribution}`

await fs.rm(outputDirectory, { force: true, recursive: true })
const tmpDir = path.join(outputDirectory, 'tmp')
await fs.mkdir(tmpDir, { recursive: true })

await Promise.all([
    installSwf(),
    installRuffle(),
    installPython(),
    installServer(),
]);

async function installSwf() {
    const dir = path.join(outputDirectory, 'swf')
    await fs.mkdir(dir, { recursive: true })
    await fs.writeFile(path.join(dir, 'quadradius_game.swf'), await download(gameSwfUrl))
    await fs.writeFile(path.join(dir, 'quadradius_lobby.swf'), await download(lobbySwfUrl))
}

async function installRuffle() {
    const dir = path.join(outputDirectory, 'ruffle')
    const archiveFile = path.join(tmpDir, ruffleDistribution)
    await fs.mkdir(dir, { recursive: true })
    await fs.writeFile(archiveFile, await download(ruffleUrl))
    if (ruffleFormat === 'tar.gz') {
        tar.extract({
            sync: true,
            file: archiveFile,
            cwd: dir,
        }, ['ruffle'])
    } else {
        fsPlain.createReadStream(archiveFile).pipe(unzip.Extract({ path: dir }))
    }
}

async function installPython() {
    const dir = path.join(outputDirectory, 'python')
    const tarGzFile = path.join(tmpDir, pythonDistribution)
    await fs.mkdir(dir, { recursive: true })
    await fs.writeFile(tarGzFile, await download(pythonDistributionUrl))
    tar.extract({
        sync: true,
        file: tarGzFile,
        cwd: dir,
        strip: 1,
    }, ['python'])

    const pythonExecutable = path.join(dir, platform == 'win32' ? 'python.exe' : 'bin/python3')
    await exec(`"${pythonExecutable}" -m pip install -r ../server/requirements.txt`)
}

async function installServer() {
    const dir = path.join(outputDirectory, 'server')
    await fs.mkdir(dir, { recursive: true })
    await fs.cp('../server/QRServer', path.join(dir, 'QRServer'), { recursive: true })
}
