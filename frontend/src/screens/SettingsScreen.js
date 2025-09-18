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
import { colors, typography, spacing, borderRadius } from '../styles/theme';

const avatarOptions = [
  'https://ui-avatars.com/api/?name=User&background=1a1a1a&color=fff',
  'https://ui-avatars.com/api/?name=User&background=374151&color=fff',
  'https://ui-avatars.com/api/?name=User&background=6b7280&color=fff',
  'https://ui-avatars.com/api/?name=User&background=9ca3af&color=000',
  'https://ui-avatars.com/api/?name=User&background=d1d5db&color=000',
  'https://ui-avatars.com/api/?name=User&background=f3f4f6&color=000',
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
    setName(newName);
    const encodedName = encodeURIComponent(newName || 'User');
    const currentBg = selectedAvatar.split('background=')[1]?.split('&')[0] || '1a1a1a';
    const currentColor = selectedAvatar.split('color=')[1] || 'fff';
    setSelectedAvatar(`https://ui-avatars.com/api/?name=${encodedName}&background=${currentBg}&color=${currentColor}`);
  };

  const selectAvatar = (avatar) => {
    const encodedName = encodeURIComponent(name || 'User');
    const bgColor = avatar.split('background=')[1]?.split('&')[0];
    const textColor = avatar.split('color=')[1];
    setSelectedAvatar(`https://ui-avatars.com/api/?name=${encodedName}&background=${bgColor}&color=${textColor}`);
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <TouchableOpacity 
        style={styles.backButton}
        onPress={() => navigation.goBack()}
      >
        <Text style={styles.backButtonText}>◀</Text>
      </TouchableOpacity>
      <Text style={styles.headerTitle}>Settings</Text>
      <View style={styles.headerRight} />
    </View>
  );

  return (
    <LinearGradient colors={colors.gradient.dark} style={styles.container}>
      {renderHeader()}
      <KeyboardAvoidingView 
        style={styles.content}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <Animatable.View 
            animation="fadeInUp" 
            duration={800}
            style={styles.profileSection}
          >
            <View style={styles.avatarContainer}>
              <Image source={{ uri: selectedAvatar }} style={styles.currentAvatar} />
            </View>
            <Text style={styles.profileTitle}>Profile Settings</Text>
            <Text style={styles.profileSubtitle}>Customize your profile information</Text>
          </Animatable.View>

          <Animatable.View 
            animation="fadeInUp" 
            duration={800}
            delay={200}
            style={styles.formSection}
          >
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Display Name</Text>
              <TextInput
                style={styles.textInput}
                value={name}
                onChangeText={updateAvatarWithName}
                placeholder="Enter your name"
                placeholderTextColor={colors.text.secondary}
                autoCapitalize="words"
                autoCorrect={false}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Avatar Style</Text>
              <Text style={styles.inputDescription}>Choose your profile picture style</Text>
              <View style={styles.avatarGrid}>
                {avatarOptions.map((avatar, index) => {
                  const encodedName = encodeURIComponent(name || 'User');
                  const bgColor = avatar.split('background=')[1]?.split('&')[0];
                  const textColor = avatar.split('color=')[1];
                  const avatarUrl = `https://ui-avatars.com/api/?name=${encodedName}&background=${bgColor}&color=${textColor}`;
                  
                  return (
                    <TouchableOpacity
                      key={index}
                      style={[
                        styles.avatarOption,
                        selectedAvatar.includes(bgColor) && styles.selectedAvatar
                      ]}
                      onPress={() => selectAvatar(avatar)}
                    >
                      <Image source={{ uri: avatarUrl }} style={styles.avatarImage} />
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>
          </Animatable.View>

          <Animatable.View 
            animation="fadeInUp" 
            duration={800}
            delay={400}
            style={styles.infoSection}
          >
            <View style={styles.infoCard}>
              <Text style={styles.infoTitle}>About SIMS AI</Text>
              <Text style={styles.infoText}>
                Your intelligent healthcare assistant powered by advanced AI technology. 
                Get instant answers to medical questions and healthcare guidance.
              </Text>
            </View>
            
            <View style={styles.infoCard}>
              <Text style={styles.infoTitle}>Privacy & Security</Text>
              <Text style={styles.infoText}>
                Your conversations are processed securely. We prioritize your privacy 
                and never store personal medical information.
              </Text>
            </View>
          </Animatable.View>
        </ScrollView>

        <Animatable.View 
          animation="fadeInUp" 
          duration={800}
          delay={600}
          style={styles.footer}
        >
          <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
            <View style={styles.saveButtonContent}>
              <Text style={styles.saveButtonText}>Save Changes</Text>
              <Text style={styles.saveButtonIcon}>✓</Text>
            </View>
          </TouchableOpacity>
        </Animatable.View>
      </KeyboardAvoidingView>
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
    fontSize: typography.sizes.lg,
    color: colors.text.primary,
    fontWeight: typography.weights.bold,
    textAlign: 'center',
  },
  headerRight: {
    width: 40,
  },
  content: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.xl,
  },
  profileSection: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
  avatarContainer: {
    marginBottom: spacing.lg,
  },
  currentAvatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 3,
    borderColor: colors.surface,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 8,
  },
  profileTitle: {
    fontSize: typography.sizes.xl,
    color: colors.text.primary,
    fontWeight: typography.weights.bold,
    marginBottom: spacing.xs,
  },
  profileSubtitle: {
    fontSize: typography.sizes.sm,
    color: colors.text.secondary,
    textAlign: 'center',
  },
  formSection: {
    marginBottom: spacing.xl,
  },
  inputGroup: {
    marginBottom: spacing.lg,
  },
  inputLabel: {
    fontSize: typography.sizes.sm,
    color: colors.text.primary,
    fontWeight: typography.weights.semibold,
    marginBottom: spacing.xs,
    letterSpacing: 0.5,
  },
  inputDescription: {
    fontSize: typography.sizes.xs,
    color: colors.text.secondary,
    marginBottom: spacing.md,
  },
  textInput: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: typography.sizes.sm,
    color: colors.text.primary,
    fontWeight: typography.weights.medium,
  },
  avatarGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  avatarOption: {
    width: '30%',
    aspectRatio: 1,
    borderRadius: borderRadius.md,
    borderWidth: 2,
    borderColor: 'transparent',
    overflow: 'hidden',
    marginBottom: spacing.sm,
  },
  selectedAvatar: {
    borderColor: colors.text.secondary,
  },
  avatarImage: {
    width: '100%',
    height: '100%',
  },
  infoSection: {
    marginBottom: spacing.xl,
  },
  infoCard: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  infoTitle: {
    fontSize: typography.sizes.sm,
    color: colors.text.primary,
    fontWeight: typography.weights.semibold,
    marginBottom: spacing.xs,
  },
  infoText: {
    fontSize: typography.sizes.xs,
    color: colors.text.secondary,
    lineHeight: 18,
  },
  footer: {
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.lg,
  },
  saveButton: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 6,
  },
  saveButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
  },
  saveButtonText: {
    fontSize: typography.sizes.md,
    color: colors.text.primary,
    fontWeight: typography.weights.semibold,
    marginRight: spacing.sm,
  },
  saveButtonIcon: {
    fontSize: 18,
    color: colors.text.secondary,
    fontWeight: typography.weights.bold,
  },
});

export default SettingsScreen;