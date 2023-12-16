const interfaces = require('os').networkInterfaces()

class NetworkInterfaces {
    constructor() {

    }

    listLocalIps() {
        const localIps = []
        Object.keys(interfaces).forEach(key => {
            interfaces[key].forEach(addr => {
                localIps.push(addr.address)
            })
        });
        return localIps
    }
}

export default NetworkInterfaces;
