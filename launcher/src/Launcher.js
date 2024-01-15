const { spawn } = require('child_process')
const fs = require('fs/promises')
const { v4: uuidv4 } = require('uuid')

class Launcher {
    abortController = new AbortController();
    childProcesses = []

    constructor(config, dir) {
        this.config = config
        this.dir = dir
    }

    validate(err) {
        this.validatePython(err)
        this.validateRuffle(err)
    }

    validatePython(err) {
        console.log(`Python executable: ${this.config.getPythonExecutable()}`);
        const proc = spawn(this.config.getPythonExecutable(), ['-V']);
        proc.stdout.on('data', (data) => {
            console.log(`Python version: ${data}`);
        });
        proc.on('error', (error) => {
            err(`Python does not work properly: ${error}`)
        });
        proc.on('exit', (code) => {
            if (code !== 0) {
                err('Python does not work properly')
            }
        });
    }

    validateRuffle(err) {
        console.log(`Ruffle executable: ${this.config.getRuffleExecutable()}`);
        const proc = spawn(this.config.getRuffleExecutable(), ['--version']);
        proc.stdout.on('data', (data) => {
            console.log(`Ruffle version: ${data}`);
        });
        proc.on('error', (error) => {
            err(`Ruffle does not work properly: ${error}`)
        });
        proc.on('exit', (code) => {
            if (code !== 0) {
                err(`Ruffle does not work properly, exited with code ${code}`)
            }
        });
    }

    async start(opts) {
        const id = uuidv4()
        const dir = `/var/tmp/qr/${id}`
        await fs.mkdir(dir, { recursive: true });
        console.log(`Starting instance at ${dir}`)

        const host = opts.host

        if (opts.serverMode) {
            console.log('Starting server')
            await this.startServer(id, dir, host)
        }

        this.startClient(id, dir, host)
    }

    startServer(id, dir, host, cb) {
        const serverProcess = spawn(
            this.config.getPythonExecutable(), [
            '-m', 'QRServer',
            '--bind', host,
            '--data', dir,
        ], {
            signal: this.abortController.signal,
        });
        this.childProcesses.push(serverProcess)
        this.bindEventsForBackgroundProcess(serverProcess, `server/${id}`)

        return new Promise(resolve => {
            let gameStarted = false
            let lobbyStarted = false
            serverProcess.stderr.on('data', (data) => {
                if (data && data.includes('Game started on')) {
                    gameStarted = true
                }
                if (data && data.includes('Lobby started on')) {
                    lobbyStarted = true
                }
                if (gameStarted && lobbyStarted) {
                    resolve()
                    gameStarted = false
                    lobbyStarted = false
                }
            });
        });
    }

    async startClient(id, path, host) {
        const addressData = `&myIPAddress=${host}&chatPort=3000&gamePort=3001`
        console.log(`address.txt: ${addressData}`);
        await fs.writeFile(`${path}/address.txt`, addressData);
        await fs.copyFile(`${this.config.getSwfDir()}/quadradius_lobby.swf`, `${path}/quadradius_lobby.swf`)
        await fs.copyFile(`${this.config.getSwfDir()}/quadradius_game.swf`, `${path}/quadradius_game.swf`)

        const clientProcess = spawn(
            this.config.getRuffleExecutable(), [
            '--power', 'low',
            '--no-gui',
            '--socket-allow', `${host}:3000`,
            '--socket-allow', `${host}:3001`,
            './quadradius_lobby.swf',
        ], {
            cwd: path,
            signal: this.abortController.signal,
        });
        this.childProcesses.push(clientProcess)
        this.bindEventsForBackgroundProcess(clientProcess, `client/${id}`)
    }

    bindEventsForBackgroundProcess(process, name) {
        process.stdout.on('data', (data) => {
            console.log(`[${name}/stdout] ${data}`)
        });
        process.stderr.on('data', (data) => {
            console.log(`[${name}/stderr] ${data}`)
        });
        process.on('exit', (code) => {
            console.log(`[${name}] exited with code ${code}`)
        });
        const thiz = this
        process.on('close', () => {
            const index = thiz.childProcesses.indexOf(process);
            if (index > -1) {
                thiz.childProcesses.splice(index, 1);
            }
        });
    }

    childrenAlive() {
        return this.childProcesses.length
    }

    close() {
        this.abortController.abort()
    }
}

export default Launcher;
