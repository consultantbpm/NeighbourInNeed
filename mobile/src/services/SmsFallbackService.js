import { Linking, Alert } from 'react-native';

class SmsFallbackService {
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
