import { Linking, Alert } from 'react-native';

class SmsFallbackService {
  /**
   * Construiește un mesaj SMS compact pentru fallback de urgență: coordonate + link Maps,
   * plus transcrierea (dacă există). Ținut scurt intenționat — SMS-urile lungi se pot rupe
   * în mai multe mesaje pe unele rețele.
   */
  buildEmergencyMessage(sosPayload = {}) {
    const { lat, lng } = sosPayload;
    const hasCoords = typeof lat === 'number' && typeof lng === 'number';
    const locationPart = hasCoords
      ? `https://maps.google.com/?q=${lat},${lng}`
      : 'locație indisponibilă';
    const note = sosPayload?.text ? ` ${sosPayload.text}` : '';
    return `SOS${sosPayload.uid ? ' ' + sosPayload.uid : ''}: ${locationPart}.${note}`.trim();
  }

  async sendEmergencySms(phoneNumber, message) {
    console.log(`[SmsFallback] Preparing SMS to ${phoneNumber} with message: ${message}`);

    const url = `sms:${phoneNumber}?body=${encodeURIComponent(message)}`;

    try {
      const canOpen = await Linking.canOpenURL(url);
      if (canOpen) {
        return Linking.openURL(url);
      } else {
        console.error('[SmsFallback] Cannot open SMS URL');
        Alert.alert('Eroare', 'Dispozitivul nu suportă trimiterea de SMS-uri nativ.');
      }
    } catch (error) {
      console.error('[SmsFallback] Error sending SMS:', error);
    }
  }
}

export default new SmsFallbackService();
