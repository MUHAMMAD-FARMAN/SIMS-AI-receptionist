import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TextInput, 
  TouchableOpacity, 
  ScrollView, 
  Alert,
  Image,
  KeyboardAvoidingView,
  Platform
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import { useUser } from '../context/UserContext';

const avatarOptions = [
  'https://ui-avatars.com/api/?name=User&background=6366f1&color=fff',
  'https://ui-avatars.com/api/?name=User&background=ec4899&color=fff',
  'https://ui-avatars.com/api/?name=User&background=10b981&color=fff',
  'https://ui-avatars.com/api/?name=User&background=f59e0b&color=fff',
  'https://ui-avatars.com/api/?name=User&background=ef4444&color=fff',
  'https://ui-avatars.com/api/?name=User&background=8b5cf6&color=fff',
];

const SettingsScreen = ({ navigation }) => {
  const { user, updateUser } = useUser();
  const [name, setName] = useState(user.name);
  const [selectedAvatar, setSelectedAvatar] = useState(user.avatar);

  const handleSave = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter a name');
      return;
    }

    await updateUser({
      name: name.trim(),
      avatar: selectedAvatar,
    });

    Alert.alert(
      'Success',
      'Your settings have been saved!',
      [{ text: 'OK', onPress: () => navigation.goBack() }]
    );
  };

  const updateAvatarWithName = (newName) => {
    const baseUrl = selectedAvatar.split('?')[0];
    const backgroundColor = selectedAvatar.match(/background=([^&]*)/)?.[1] || '6366f1';
    const newAvatar = `${baseUrl}?name=${encodeURIComponent(newName || 'User')}&background=${backgroundColor}&color=fff`;
    setSelectedAvatar(newAvatar);
  };

  const selectAvatarColor = (avatar) => {
    const backgroundColor = avatar.match(/background=([^&]*)/)?.[1] || '6366f1';
    const baseUrl = avatar.split('?')[0];
    const newAvatar = `${baseUrl}?name=${encodeURIComponent(name || 'User')}&background=${backgroundColor}&color=fff`;
    setSelectedAvatar(newAvatar);
  };

  return (
    <LinearGradient
      colors={['#f9fafb', '#f3f4f6']}
      style={styles.container}
    >
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        <ScrollView 
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <Animatable.View 
            animation="fadeInUp" 
            duration={800}
            style={styles.content}
          >
            {/* Current Avatar */}
            <View style={styles.currentAvatarContainer}>
              <Image 
                source={{ uri: selectedAvatar }}
                style={styles.currentAvatar}
              />
              <Text style={styles.currentAvatarLabel}>Current Avatar</Text>
            </View>

            {/* Name Input */}
            <View style={styles.inputContainer}>
              <Text style={styles.label}>Display Name</Text>
              <TextInput
                style={styles.input}
                value={name}
                onChangeText={(text) => {
                  setName(text);
                  updateAvatarWithName(text);
                }}
                placeholder="Enter your name"
                placeholderTextColor="#9ca3af"
              />
            </View>

            {/* Avatar Selection */}
            <View style={styles.avatarSection}>
              <Text style={styles.label}>Choose Avatar Color</Text>
              <View style={styles.avatarGrid}>
                {avatarOptions.map((avatar, index) => {
                  const backgroundColor = avatar.match(/background=([^&]*)/)?.[1];
                  const currentBgColor = selectedAvatar.match(/background=([^&]*)/)?.[1];
                  const isSelected = backgroundColor === currentBgColor;
                  
                  return (
                    <TouchableOpacity
                      key={index}
                      style={[
                        styles.avatarOption,
                        isSelected && styles.avatarOptionSelected
                      ]}
                      onPress={() => selectAvatarColor(avatar)}
                    >
                      <Image 
                        source={{ 
                          uri: `https://ui-avatars.com/api/?name=${encodeURIComponent(name || 'User')}&background=${backgroundColor}&color=fff`
                        }}
                        style={styles.avatarImage}
                      />
                      {isSelected && (
                        <View style={styles.checkmark}>
                          <Text style={styles.checkmarkText}>✓</Text>
                        </View>
                      )}
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>

            {/* Save Button */}
            <TouchableOpacity
              style={styles.saveButton}
              onPress={handleSave}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#6366f1', '#8b5cf6']}
                style={styles.saveButtonGradient}
              >
                <Text style={styles.saveButtonText}>Save Changes</Text>
              </LinearGradient>
            </TouchableOpacity>

            {/* Cancel Button */}
            <TouchableOpacity
              style={styles.cancelButton}
              onPress={() => navigation.goBack()}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
          </Animatable.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingVertical: 20,
  },
  content: {
    paddingHorizontal: 20,
  },
  currentAvatarContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  currentAvatar: {
    width: 120,
    height: 120,
    borderRadius: 60,
    marginBottom: 10,
    borderWidth: 3,
    borderColor: '#6366f1',
  },
  currentAvatarLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  inputContainer: {
    marginBottom: 30,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 10,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    color: '#111827',
  },
  avatarSection: {
    marginBottom: 30,
  },
  avatarGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  avatarOption: {
    width: '30%',
    aspectRatio: 1,
    marginBottom: 15,
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  avatarOptionSelected: {
    borderColor: '#6366f1',
  },
  avatarImage: {
    width: '100%',
    height: '100%',
  },
  checkmark: {
    position: 'absolute',
    bottom: 5,
    right: 5,
    backgroundColor: '#6366f1',
    borderRadius: 12,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkmarkText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  saveButton: {
    marginBottom: 15,
  },
  saveButtonGradient: {
    paddingVertical: 15,
    borderRadius: 12,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  cancelButton: {
    paddingVertical: 15,
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#6b7280',
    fontSize: 16,
  },
});

export default SettingsScreen;