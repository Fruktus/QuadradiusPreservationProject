const path = require('path')

class Config {
    constructor(queryParams) {
        this.isPackaged = queryParams.get('isPackaged') === 'true'
        this.appPath = queryParams.get('appPath')
        this.resourcesPath = process.resourcesPath
    }

    getPythonExecutable() {
        const file = process.platform === 'win32' ? 'python.exe' : 'bin/python3'

        if (this.isPackaged) {
            return path.join(this.resourcesPath, 'python', file)
        } else {
            return path.join(__dirname, '../extras/python', file)
        }
    }

    getRuffleExecutable() {
        if (this.isPackaged) {
            return path.join(this.resourcesPath, 'ruffle/ruffle')
        } else {
            return path.join(__dirname, '../extras/ruffle/ruffle')
        }
    }

    getServerDir() {
        if (this.isPackaged) {
            return path.join(this.resourcesPath, 'server')
        } else {
            return path.join(__dirname, '../extras/server')
        }
    }

    getSwfDir() {
        if (this.isPackaged) {
            return path.join(this.resourcesPath, 'swf')
        } else {
            return path.join(__dirname, '../extras/swf')
        }
    }

    toString() {
        return JSON.stringify(this)
    }
}

export default Config;
