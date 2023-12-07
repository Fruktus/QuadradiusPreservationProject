const bs60 = require('base-x')('0123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz_')
const gzip = require('gzip-js')

class Invite {
    constructor(invite) {
        this.obj = invite ? this.decode(invite) : {}
    }

    decode(invite) {
        const baseDecoded = bs60.decode(invite)
        const unzipped = baseDecoded //gzip.unzip(baseDecoded);
        const unzippedString = String.fromCodePoint(...unzipped)
        console.log(unzippedString)
        return JSON.parse(unzippedString)
    }

    encode() {
        const str = JSON.stringify(this.obj)
        // const gzipped = gzip.zip(str, {
        //     level: 9,
        // })
        const gzipped = Array.from(str, c => c.codePointAt(0))
        return bs60.encode(gzipped)
    }
}

export default Invite;
