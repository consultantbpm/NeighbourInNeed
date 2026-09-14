import WearDataLayerService from './WearDataLayerService';
import SmsFallbackService from './SmsFallbackService';

class AlertRoutingService {
  constructor() {
    this.emergencyContact = "112";
    this.isInternetAvailable = true; 
  }

  initialize() {
    console.log('[AlertRoutingService] Initializing...');
    WearDataLayerService.connect();
    WearDataLayerService.subscribeToAlerts(this.routeAlert);
  }

  routeAlert = (alertEvent) => {
    const { type, payload } = alertEvent || {};
    
    if (type === 'VOICE_SOS') {
      this.handleVoiceSos(payload);
    } else {
      console.warn('[AlertRoutingService] Unknown alert type:', type);
    }
  }

  handleVoiceSos(payload) {
    console.log('[AlertRoutingService] Routing Voice SOS:', payload);
    
    if (this.isInternetAvailable) {
      this.sendToBackend(payload);
    } else {
      console.log('[AlertRoutingService] Internet down. Using SMS Fallback.');
      const message = `SOS! Am nevoie de ajutor! Locație: ${payload?.location || 'Necunoscută'}. Mesaj: ${payload?.transcription || 'Fără detalii'}`;
      SmsFallbackService.sendEmergencySms(this.emergencyContact, message);
    }
  }

  sendToBackend(payload) {
    console.log('[AlertRoutingService] Sending alert to backend via mDNS...', payload);
    const backendUrl = 'http://ai-dispatcher.local:8000/api/dispatch';
    
    fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => console.log('[AlertRoutingService] Success from AI:', data))
    .catch(error => {
      console.error('[AlertRoutingService] Error hitting mDNS backend:', error);
      // Fallback in caz ca mDNS pica
      SmsFallbackService.sendEmergencySms(this.emergencyContact, "Eroare retea locala! Urgenta!");
    });
  }
  
  setInternetStatus(status) {
    this.isInternetAvailable = status;
  }
}

export default new AlertRoutingService();
