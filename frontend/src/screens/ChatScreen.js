import React, { useState, useCallback, useEffect } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, Alert, TouchableOpacity } from 'react-native';
import { GiftedChat, Bubble, InputToolbar, Send } from 'react-native-gifted-chat';
import { LinearGradient } from 'expo-linear-gradient';
import uuid from 'react-native-uuid';
import { useUser } from '../context/UserContext';
import { BACKEND_URL } from '../config/config';
import { colors, typography, spacing, borderRadius } from '../styles/theme';
import NetInfo from '@react-native-community/netinfo';

const ChatScreen = ({ navigation }) => {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [debugInfo, setDebugInfo] = useState('Ready');
  const [networkInfo, setNetworkInfo] = useState('Checking...');
  const { user } = useUser();

  useEffect(() => {
    // Welcome message
    setMessages([
      {
        _id: uuid.v4(),
        text: 'Hello! I\'m your AI healthcare assistant. How can I help you today?',
        createdAt: new Date(),
        user: {
          _id: 2,
          name: 'AI Assistant',
          avatar: 'https://ui-avatars.com/api/?name=AI&background=1a1a1a&color=fff',
        },
        system: false,
      },
    ]);

    // Check network status for APK debugging
    NetInfo.fetch().then(state => {
      setNetworkInfo(`${state.type} - ${state.isConnected ? 'Connected' : 'Disconnected'}`);
      console.log('Network Info:', state);
    }).catch(error => {
      setNetworkInfo('Network info unavailable');
      console.log('NetInfo error:', error);
    });
  }, []);

  const sendQueryToBackend = async (userMessage) => {
    try {
      const url = `${BACKEND_URL}/query`;
      setDebugInfo(`Connecting to: ${url}`);
      console.log('Attempting to connect to:', url);
      console.log('Platform:', Platform.OS);
      console.log('Network:', networkInfo);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage,
        }),
        timeout: 15000, // Increased timeout for APK
      });

      setDebugInfo(`Response: ${response.status} ${response.ok ? 'OK' : 'Error'}`);
      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Response data:', data);
      setDebugInfo('Connected successfully');
      
      return data.answer || 'I apologize, but I couldn\'t process your request at the moment.';
    } catch (error) {
      const errorMsg = error.message || 'Unknown error';
      setDebugInfo(`Error: ${errorMsg}`);
      console.error('Backend connection error:', error);
      
      // Enhanced error message for APK debugging
      const platformInfo = Platform.OS === 'android' ? 'Android APK' : Platform.OS;
      Alert.alert(
        'Connection Error',
        `Network error: Cannot reach the server. Check if the backend is running.\n\nPlatform: ${platformInfo}\nNetwork: ${networkInfo}\nTrying to connect to: ${BACKEND_URL}\nError: ${errorMsg}`,
        [{ text: 'OK' }]
      );
      return 'I\'m sorry, I\'m having trouble connecting right now. Please try again in a moment.';
    }
  };

  const onSend = useCallback(async (messages = []) => {
    const userMessage = messages[0];
    
    // Add user message immediately
    setMessages(previousMessages => GiftedChat.append(previousMessages, messages));
    
    // Show typing indicator
    setIsTyping(true);
    
    try {
      const botResponse = await sendQueryToBackend(userMessage.text);
      
      // Create bot message
      const botMessage = {
        _id: uuid.v4(),
        text: botResponse,
        createdAt: new Date(),
        user: {
          _id: 2,
          name: 'AI Assistant',
          avatar: 'https://ui-avatars.com/api/?name=AI&background=1a1a1a&color=fff',
        },
      };
      
      // Add bot message
      setMessages(previousMessages => GiftedChat.append(previousMessages, [botMessage]));
    } catch (error) {
      console.error('Error in onSend:', error);
    } finally {
      setIsTyping(false);
    }
  }, []);

  const renderBubble = (props) => {
    return (
      <Bubble
        {...props}
        wrapperStyle={{
          right: {
            backgroundColor: colors.surface,
            borderWidth: 1,
            borderColor: colors.border,
          },
          left: {
            backgroundColor: colors.background,
            borderWidth: 1,
            borderColor: colors.border,
          },
        }}
        textStyle={{
          right: {
            color: colors.text.primary,
            fontSize: typography.sizes.sm,
            fontWeight: typography.weights.medium,
          },
          left: {
            color: colors.text.primary,
            fontSize: typography.sizes.sm,
            fontWeight: typography.weights.medium,
          },
        }}
        timeTextStyle={{
          right: {
            color: colors.text.secondary,
            fontSize: typography.sizes.xs,
          },
          left: {
            color: colors.text.secondary,
            fontSize: typography.sizes.xs,
          },
        }}
      />
    );
  };

  const renderInputToolbar = (props) => {
    return (
      <InputToolbar
        {...props}
        containerStyle={styles.inputToolbar}
        primaryStyle={styles.inputPrimary}
      />
    );
  };

  const renderSend = (props) => {
    return (
      <Send {...props}>
        <View style={styles.sendButton}>
          <Text style={styles.sendButtonText}>▶</Text>
        </View>
      </Send>
    );
  };

  const testConnection = async () => {
    setDebugInfo('Testing connection...');
    try {
      // Test basic network connectivity first
      const testResponse = await fetch('https://httpbin.org/get', {
        method: 'GET',
        timeout: 5000,
      });
      console.log('HTTPS test:', testResponse.status);
      
      // Then test our backend
      const response = await fetch(`${BACKEND_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'test' }),
        timeout: 10000,
      });
      setDebugInfo(`Test: ${response.status} ${response.ok ? 'OK' : 'Failed'}`);
    } catch (error) {
      setDebugInfo(`Test failed: ${error.message}`);
      console.log('Connection test error:', error);
    }
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <TouchableOpacity 
        style={styles.backButton}
        onPress={() => navigation.goBack()}
      >
        <Text style={styles.backButtonText}>◀</Text>
      </TouchableOpacity>
      <View style={styles.headerTitle}>
        <Text style={styles.headerTitleText}>AI Assistant</Text>
        <Text style={styles.headerSubtitle}>{debugInfo} | {networkInfo}</Text>
      </View>
      <View style={styles.headerRight}>
        <TouchableOpacity onPress={testConnection} style={styles.testButton}>
          <Text style={styles.testButtonText}>Test</Text>
        </TouchableOpacity>
        <View style={styles.statusIndicator} />
      </View>
    </View>
  );

  return (
    <LinearGradient colors={colors.gradient.dark} style={styles.container}>
      {renderHeader()}
      <View style={styles.chatContainer}>
        <GiftedChat
          messages={messages}
          onSend={onSend}
          user={{
            _id: 1,
            name: user.name,
            avatar: user.avatar,
          }}
          isTyping={isTyping}
          renderBubble={renderBubble}
          renderInputToolbar={renderInputToolbar}
          renderSend={renderSend}
          alwaysShowSend
          scrollToBottom
          showUserAvatar={false}
          showAvatarForEveryMessage={true}
          textInputStyle={styles.textInput}
          placeholder="Type your message..."
          placeholderTextColor={colors.text.secondary}
          messagesContainerStyle={styles.messagesContainer}
          keyboardShouldPersistTaps="never"
          bottomOffset={Platform.OS === 'ios' ? 0 : 0}
        />
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 50,
    paddingBottom: spacing.md,
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    justifyContent: 'center',
    alignItems: 'center',
  },
  backButtonText: {
    fontSize: 20,
    color: colors.text.primary,
    fontWeight: typography.weights.bold,
  },
  headerTitle: {
    flex: 1,
    marginLeft: spacing.md,
  },
  headerTitleText: {
    fontSize: typography.sizes.lg,
    color: colors.text.primary,
    fontWeight: typography.weights.bold,
  },
  headerSubtitle: {
    fontSize: typography.sizes.xs,
    color: colors.text.secondary,
    marginTop: 2,
  },
  headerRight: {
    alignItems: 'center',
    flexDirection: 'row',
  },
  testButton: {
    backgroundColor: colors.surface,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginRight: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  testButtonText: {
    color: colors.text.primary,
    fontSize: 10,
    fontWeight: 'bold',
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10B981', // Green for online
  },
  chatContainer: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  messagesContainer: {
    backgroundColor: 'transparent',
    paddingHorizontal: spacing.xs,
  },
  inputToolbar: {
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    marginHorizontal: spacing.sm,
    marginBottom: spacing.sm,
    borderRadius: borderRadius.lg,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  inputPrimary: {
    alignItems: 'center',
  },
  textInput: {
    color: colors.text.primary,
    fontSize: typography.sizes.sm,
    fontWeight: typography.weights.medium,
    lineHeight: 20,
    marginTop: Platform.OS === 'ios' ? 6 : 0,
    marginBottom: Platform.OS === 'ios' ? 6 : 0,
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: borderRadius.md,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.xs,
    marginBottom: spacing.xs,
  },
  sendButtonText: {
    fontSize: 18,
    color: colors.text.primary,
    fontWeight: typography.weights.bold,
  },
});

export default ChatScreen;