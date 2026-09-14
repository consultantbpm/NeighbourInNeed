import { DeviceEventEmitter } from 'react-native';

class WearDataLayerService {
  constructor() {
    this.listeners = [];
  }

  // Initialize connection with the wear data layer
  connect() {
    console.log('[WearDataLayer] Connecting to smartwatch data layer...');
    // Mock connection logic for hackathon
    this.messageListener = DeviceEventEmitter.addListener('onWearMessageReceived', this.handleIncomingMessage);
  }

  handleIncomingMessage = (event) => {
    console.log('[WearDataLayer] Received message:', event);
    this.listeners.forEach(listener => listener(event));
  }

  subscribeToAlerts(callback) {
    this.listeners.push(callback);
  }

  disconnect() {
    if (this.messageListener) {
      this.messageListener.remove();
    }
    this.listeners = [];
  }
}

export default new WearDataLayerService();
