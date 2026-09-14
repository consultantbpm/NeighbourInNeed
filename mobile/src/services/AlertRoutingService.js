import WearDataLayerService from './WearDataLayerService';
import SmsFallbackService from './SmsFallbackService';

const BACKEND_URL = 'http://ai-dispatcher.local:8000/sos';
const REQUEST_TIMEOUT_MS = 4000;
// Un singur retry pe mDNS înainte de a trece la SMS (cerință: "retry o dată").
const MAX_MDNS_ATTEMPTS = 2;

class AlertRoutingService {
  constructor() {
    this.emergencyContact = '112';
    this.isInternetAvailable = true;
    // Jurnal local al încercărilor de rutare pentru un tichet, cel mai recent ultimul.
    // Ținut doar în memorie (nu persistă) — suficient pentru demo/debug.
    this.attemptLog = [];
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
  };

  _logAttempt(step, detail) {
    const entry = { step, detail, at: new Date().toISOString() };
    this.attemptLog.push(entry);
    console.log(`[AlertRoutingService] [${step}]`, detail);
  }

  /**
   * Normalizează payload-ul primit de la ceas/telefon la contractul de sârmă fixat de director
   * (vezi backend_python/dispatcher.py: validate_sos_payload) — POST /sos:
   * {source: "watch_button"|"phone_button"|"phone_sms_fallback", group_id, uid, lat, lng,
   *  text opțional, ts opțional}. Comun cu aplicația Kotlin telefon/ceas.
   */
  buildSosPayload(payload) {
    return {
      group_id: payload?.groupId ?? payload?.group_id,
      uid: payload?.uid,
      source: payload?.source || 'watch_button',
      lat: payload?.lat,
      lng: payload?.lng,
      text: payload?.transcription || payload?.text || undefined,
      ts: payload?.ts || new Date().toISOString(),
    };
  }

  async handleVoiceSos(payload) {
    // Pasul 1 (data layer) s-a întâmplat deja — alerta a ajuns aici prin WearDataLayerService.
    this._logAttempt('data_layer', 'alertă primită de la ceas/telefon');

    const sosPayload = this.buildSosPayload(payload);

    if (!this.isInternetAvailable) {
      this._logAttempt('retea', 'fără internet — sar direct la SMS');
      await this.sendSms(sosPayload);
      return;
    }

    // Pasul 2: mDNS HTTP către dispecerul local, cu un retry unic.
    const delivered = await this.sendToBackendWithRetry(sosPayload);

    // Pasul 3: dacă mDNS a eșuat de tot, SMS.
    if (!delivered) {
      await this.sendSms(sosPayload);
    }
  }

  async sendToBackendWithRetry(sosPayload) {
    for (let attempt = 1; attempt <= MAX_MDNS_ATTEMPTS; attempt++) {
      this._logAttempt('mdns_http', `încercarea ${attempt}/${MAX_MDNS_ATTEMPTS}`);
      const ok = await this.sendToBackend(sosPayload);
      if (ok) {
        return true;
      }
    }
    return false;
  }

  async sendToBackend(sosPayload) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(BACKEND_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sosPayload),
        signal: controller.signal,
      });

      if (!response.ok) {
        this._logAttempt('mdns_http_esuat', `status HTTP ${response.status}`);
        return false;
      }

      const data = await response.json();
      this._logAttempt('mdns_http_succes', data);
      return true;
    } catch (error) {
      this._logAttempt('mdns_http_eroare', error?.message || String(error));
      return false;
    } finally {
      clearTimeout(timer);
    }
  }

  async sendSms(sosPayload) {
    this._logAttempt('sms_fallback', 'trimit SMS de urgență');
    const message = SmsFallbackService.buildEmergencyMessage(sosPayload);
    await SmsFallbackService.sendEmergencySms(this.emergencyContact, message);
  }

  setInternetStatus(status) {
    this.isInternetAvailable = status;
  }
}

export default new AlertRoutingService();
