const { ipcRenderer } = require('electron')

import React, { Component } from 'react';
import './App.css';
import NetworkInterfaces from './NetworkInterfaces.js';
import Config from './Config.js';
import Launcher from './Launcher.js';

class App extends Component {
    serverModeRef = React.createRef();
    serverHostRef = React.createRef();
    tabsRef = React.createRef();

    constructor(props) {
        super(props);
        this.queryParams = new URLSearchParams(document.location.search)
        this.config = new Config(this.queryParams)
        this.launcher = new Launcher(this.config, '/var/tmp/qr')

        this.state = {
            errorMessages: [],
            serverMode: false,
            loading: false,
        };

        const thiz = this
        ipcRenderer.on('destroy', function (event, interrupted) {
            if (!interrupted && thiz.launcher.childrenAlive() > 0) {
                ipcRenderer.send(
                    'ask',
                    'force-destroy',
                    'Confirm exit',
                    'Are you sure you want to exit? All spawned games and servers will be killed.',
                    ['No', 'Yes'])
                return
            }
            thiz.destroy()
            ipcRenderer.send('destroyed')
        });

        ipcRenderer.on('force-destroy', function (event, response) {
            if (response == 1) {
                thiz.destroy()
                ipcRenderer.send('destroyed')
            }
        });
    }

    componentDidMount() {
        console.log('Config:')
        console.log(this.config)
        this.launcher.validate((err) => {
            this.addErrorMessage(err)
        })
    }

    addErrorMessage(message) {
        this.setState({
            errorMessages: [...this.state.errorMessages, message],
        })
    }

    async start() {
        this.setState({ loading: true })
        await this.launcher.start({
            host: this.serverHostRef.current.value,
            serverMode: this.serverModeRef.current.toggled,
        })
        this.setState({ loading: false })
        ipcRenderer.send('set-destroyable')
    }

    destroy() {
        console.log('Exiting')
        this.launcher.close()
    }

    render() {
        return (
            <x-box vertical={true} class="main-container">
                <x-box vertical={true}>
                    {this.renderMessages()}
                </x-box>
                <x-switch ref={this.serverModeRef}>
                    <x-label>Server mode</x-label>
                </x-switch>
                <x-input ref={this.serverHostRef} style={{ marginTop: '7px' }}>
                    <x-label>Server host</x-label>
                </x-input>
                <x-box style={{ marginTop: '7px' }}>
                    <x-button onClick={() => this.lookupIp()}>
                        <x-label>Lookup public IP</x-label>
                    </x-button>
                    <x-button style={{ marginLeft: '7px' }}>
                        <x-label>Use local IP</x-label>
                        {this.renderLocalIps()}
                    </x-button>
                    <x-button onClick={() => this.start()} style={{ marginLeft: '7px' }}>
                        {this.state.loading ? <x-throbber size="small" style={{ marginRight: '7px' }}></x-throbber> : null}
                        <x-label>Start</x-label>
                    </x-button>
                </x-box>
                <x-card>
                    <main>
                        <strong>Joining a lobby</strong>
                        <p>
                            Disable server mode and use the IP of the server&mdash;the same entered by the person hosting the lobby.
                        </p>
                    </main>
                </x-card>
                <x-card>
                    <main>
                        <strong>Hosting a lobby</strong>
                        <p>
                            Enable server mode and use an IP accessible by others.
                            For LAN games use a local IP, for Internet-based games use the public IP.
                            When using public IP note that ports 3000, 3001 need to be accessible.
                            UPnP is not supported yet, ports cannot be changed yet.
                        </p>
                    </main>
                </x-card>
            </x-box>
        );
    }

    renderMessages() {
        const messages = []
        this.state.errorMessages.forEach((msg) => {
            messages.push(<x-card>
                <main>
                    <p>{msg}</p>
                </main>
            </x-card>)
        })
        return messages
    }

    renderLocalIps() {
        const ni = new NetworkInterfaces()
        const items = []
        ni.listLocalIps().forEach((ip) => {
            items.push(<x-menuitem onClick={() => this.setServerHost(ip)}>
                <x-label>{ip}</x-label>
            </x-menuitem>)
        })
        return (<x-menu>
            {items}
        </x-menu>)
    }

    lookupIp() {
        const thiz = this
        var Client = require('node-rest-client').Client
        var client = new Client()
        client.get("https://ifconfig.me/all.json", function (data, response) {
            thiz.setServerHost(data['ip_addr'])
        });
    }

    setServerHost(serverHost) {
        this.serverHostRef.current.value = serverHost
    }
}

export default App;
