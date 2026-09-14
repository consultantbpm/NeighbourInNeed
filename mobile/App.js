import React, { useEffect } from 'react';
import { SafeAreaView, Text, StyleSheet } from 'react-native';
import AlertRoutingService from './src/services/AlertRoutingService';

export default function App() {
  useEffect(() => {
    AlertRoutingService.initialize();
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>Neighbour In Need</Text>
      <Text>Mobile App Skeleton Initialized</Text>
      <Text>Smartwatch Companion Active</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  }
});
