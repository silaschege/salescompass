/**
 * SalesCompass WebRTC Softphone
 * Browser-based phone using SIP.js
 * 
 * Dependencies: SIP.js (https://sipjs.com/)
 */

class SalesCompassSoftphone {
    constructor(options = {}) {
        this.server = options.server || window.WAZO_WSS_URL || window.location.hostname;
        this.extension = options.extension;
        this.password = options.password;
        this.displayName = options.displayName || 'SalesCompass';

        this.userAgent = null;
        this.registerer = null;
        this.currentSession = null;
        this.isRegistered = false;
        this.isMuted = false;
        this.isOnHold = false;

        // Callbacks
        this.onStateChange = options.onStateChange || (() => { });
        this.onIncomingCall = options.onIncomingCall || (() => { });
        this.onCallEnded = options.onCallEnded || (() => { });
        this.onRegistered = options.onRegistered || (() => { });
        this.onUnregistered = options.onUnregistered || (() => { });

        // ICE servers
        this.iceServers = options.iceServers || [
            { urls: 'stun:stun.l.google.com:19302' }
        ];
    }

    /**
     * Initialize and register the softphone
     */
    async initialize() {
        if (!window.SIP) {
            console.error('SIP.js not loaded. Include: https://cdn.jsdelivr.net/npm/sip.js/lib/sip.min.js');
            return false;
        }

        if (!this.extension || !this.password) {
            console.error('Extension and password are required');
            return false;
        }

        try {
            const uri = SIP.UserAgent.makeURI(`sip:${this.extension}@${this.server}`);

            this.userAgent = new SIP.UserAgent({
                uri: uri,
                transportOptions: {
                    server: `wss://${this.server}:8089/ws`
                },
                authorizationPassword: this.password,
                authorizationUsername: this.extension,
                displayName: this.displayName,
                sessionDescriptionHandlerFactoryOptions: {
                    peerConnectionConfiguration: {
                        iceServers: this.iceServers
                    },
                    constraints: {
                        audio: true,
                        video: false
                    }
                }
            });

            // Handle incoming calls
            this.userAgent.delegate = {
                onInvite: (invitation) => this._handleIncomingCall(invitation)
            };

            // Start the user agent
            await this.userAgent.start();

            // Register
            this.registerer = new SIP.Registerer(this.userAgent);
            this.registerer.stateChange.addListener((state) => {
                if (state === SIP.RegistererState.Registered) {
                    this.isRegistered = true;
                    this._updateUI('ready');
                    this.onRegistered();
                } else if (state === SIP.RegistererState.Unregistered) {
                    this.isRegistered = false;
                    this._updateUI('offline');
                    this.onUnregistered();
                }
            });

            await this.registerer.register();

            console.log('Softphone initialized successfully');
            return true;

        } catch (error) {
            console.error('Failed to initialize softphone:', error);
            this._updateUI('error');
            return false;
        }
    }

    /**
     * Make an outbound call
     */
    async call(destination) {
        if (!this.userAgent || !this.isRegistered) {
            console.error('Softphone not ready');
            return null;
        }

        if (this.currentSession) {
            console.warn('Already in a call');
            return null;
        }

        try {
            const target = SIP.UserAgent.makeURI(`sip:${destination}@${this.server}`);
            const inviter = new SIP.Inviter(this.userAgent, target);

            inviter.stateChange.addListener((state) => {
                this._handleSessionState(state);
            });

            await inviter.invite({
                requestDelegate: {
                    onAccept: () => {
                        this._setupRemoteMedia(inviter);
                    }
                }
            });

            this.currentSession = inviter;
            this._updateUI('calling');

            return inviter;

        } catch (error) {
            console.error('Failed to place call:', error);
            return null;
        }
    }

    /**
     * Answer an incoming call
     */
    async answer() {
        if (!this.currentSession) {
            console.warn('No incoming call to answer');
            return;
        }

        try {
            await this.currentSession.accept({
                sessionDescriptionHandlerOptions: {
                    constraints: { audio: true, video: false }
                }
            });

            this._setupRemoteMedia(this.currentSession);
            this._updateUI('connected');

        } catch (error) {
            console.error('Failed to answer call:', error);
        }
    }

    /**
     * Hang up the current call
     */
    async hangup() {
        if (!this.currentSession) {
            return;
        }

        try {
            const state = this.currentSession.state;

            if (state === SIP.SessionState.Established) {
                this.currentSession.bye();
            } else if (state === SIP.SessionState.Establishing) {
                this.currentSession.cancel();
            } else if (this.currentSession.reject) {
                this.currentSession.reject();
            }
        } catch (error) {
            console.error('Error hanging up:', error);
        }

        this.currentSession = null;
        this._updateUI('ready');
        this.onCallEnded();
    }

    /**
     * Toggle mute
     */
    toggleMute() {
        if (!this.currentSession) return;

        try {
            const pc = this.currentSession.sessionDescriptionHandler.peerConnection;
            pc.getSenders().forEach(sender => {
                if (sender.track && sender.track.kind === 'audio') {
                    sender.track.enabled = this.isMuted;
                }
            });

            this.isMuted = !this.isMuted;
            this._updateUI(this.isMuted ? 'muted' : 'connected');

        } catch (error) {
            console.error('Failed to toggle mute:', error);
        }
    }

    /**
     * Transfer call to another extension/number
     */
    async transfer(destination) {
        if (!this.currentSession) return;

        try {
            const target = SIP.UserAgent.makeURI(`sip:${destination}@${this.server}`);
            await this.currentSession.refer(target);

        } catch (error) {
            console.error('Failed to transfer:', error);
        }
    }

    /**
     * Send DTMF digit
     */
    sendDTMF(digit) {
        if (!this.currentSession) return;

        try {
            const options = {
                requestOptions: {
                    body: {
                        contentDisposition: 'render',
                        contentType: 'application/dtmf-relay',
                        content: `Signal=${digit}\r\nDuration=100`
                    }
                }
            };

            this.currentSession.info(options);

        } catch (error) {
            console.error('Failed to send DTMF:', error);
        }
    }

    /**
     * Unregister and disconnect
     */
    async disconnect() {
        if (this.currentSession) {
            await this.hangup();
        }

        if (this.registerer) {
            await this.registerer.unregister();
        }

        if (this.userAgent) {
            await this.userAgent.stop();
        }

        this.isRegistered = false;
        this._updateUI('offline');
    }

    // Private methods

    _handleIncomingCall(invitation) {
        this.currentSession = invitation;
        this._updateUI('ringing');

        const callerInfo = {
            from: invitation.remoteIdentity.uri.user,
            displayName: invitation.remoteIdentity.displayName || 'Unknown'
        };

        invitation.stateChange.addListener((state) => {
            this._handleSessionState(state);
        });

        this.onIncomingCall(callerInfo);
    }

    _handleSessionState(state) {
        console.log('Session state:', state);

        switch (state) {
            case SIP.SessionState.Establishing:
                this._updateUI('connecting');
                break;
            case SIP.SessionState.Established:
                this._updateUI('connected');
                break;
            case SIP.SessionState.Terminated:
                this.currentSession = null;
                this._updateUI('ready');
                this.onCallEnded();
                break;
        }

        this.onStateChange(state);
    }

    _setupRemoteMedia(session) {
        try {
            const remoteStream = new MediaStream();
            const pc = session.sessionDescriptionHandler.peerConnection;

            pc.getReceivers().forEach(receiver => {
                if (receiver.track) {
                    remoteStream.addTrack(receiver.track);
                }
            });

            const audioElement = document.getElementById('softphone-audio');
            if (audioElement) {
                audioElement.srcObject = remoteStream;
                audioElement.play().catch(e => console.warn('Audio play failed:', e));
            }
        } catch (error) {
            console.error('Failed to setup remote media:', error);
        }
    }

    _updateUI(state) {
        const statusElement = document.getElementById('softphone-status');
        if (statusElement) {
            statusElement.className = `softphone-status softphone-${state}`;

            const labels = {
                'offline': 'Offline',
                'ready': 'Ready',
                'calling': 'Calling...',
                'ringing': 'Incoming Call',
                'connecting': 'Connecting...',
                'connected': 'Connected',
                'muted': 'Muted',
                'error': 'Error'
            };

            statusElement.textContent = labels[state] || state;
        }
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SalesCompassSoftphone;
}
