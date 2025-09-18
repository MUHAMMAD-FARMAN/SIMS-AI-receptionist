import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';

import SplashScreen from './src/screens/SplashScreen';
import HomeScreen from './src/screens/HomeScreen';
import ChatScreen from './src/screens/ChatScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import { UserProvider } from './src/context/UserContext';

const Stack = createNativeStackNavigator();

export default function App() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate loading time for splash screen
    setTimeout(() => {
      setIsLoading(false);
    }, 2500);
  }, []);

  if (isLoading) {
    return <SplashScreen />;
  }

  return (
    <UserProvider>
      <NavigationContainer>
        <StatusBar style="light" />
        <Stack.Navigator
          initialRouteName="Home"
          screenOptions={{
            headerShown: false, // Disable all default headers
          }}
        >
          <Stack.Screen 
            name="Home" 
            component={HomeScreen}
            options={{ 
              headerShown: false 
            }}
          />
          <Stack.Screen 
            name="Chat" 
            component={ChatScreen}
            options={{ 
              headerShown: false // No default header for Chat screen
            }}
          />
          <Stack.Screen 
            name="Settings" 
            component={SettingsScreen}
            options={{ 
              headerShown: false // No default header for Settings screen
            }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </UserProvider>
  );
}
