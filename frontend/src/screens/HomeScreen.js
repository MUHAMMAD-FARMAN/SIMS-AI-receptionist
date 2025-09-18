import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Dimensions, Image, ScrollView } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import { useUser } from '../context/UserContext';
import { colors, typography, spacing, borderRadius } from '../styles/theme';

const { width, height } = Dimensions.get('window');

const HomeScreen = ({ navigation }) => {
  const { user } = useUser();

  return (
    <LinearGradient
      colors={colors.gradient.dark}
      style={styles.container}
    >
      <TouchableOpacity 
        style={styles.settingsButton}
        onPress={() => navigation.navigate('Settings')}
      >
        <View style={styles.settingsIcon}>
          <Text style={styles.settingsText}>⚙️</Text>
        </View>
      </TouchableOpacity>

      <Animatable.View 
        animation="fadeInDown" 
        duration={1000}
        style={styles.header}
      >
        <View style={styles.avatarContainer}>
          <Image 
            source={{ uri: user.avatar }}
            style={styles.avatar}
          />
        </View>
        <Text style={styles.welcomeText}>Welcome back</Text>
        <Text style={styles.userName}>{user.name}</Text>
        <Text style={styles.subtitle}>How can I assist you today?</Text>
      </Animatable.View>

      <ScrollView 
        style={styles.scrollContainer}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Animatable.View 
          animation="fadeInUp" 
          duration={1000}
          delay={300}
          style={styles.content}
        >
          <View style={styles.featuresContainer}>
            <View style={styles.featureCard}>
              <View style={styles.featureIconContainer}>
                <Text style={styles.featureIcon}>AI</Text>
              </View>
              <Text style={styles.featureTitle}>AI-Powered</Text>
              <Text style={styles.featureDesc}>Advanced RAG technology for intelligent responses</Text>
            </View>
            <View style={styles.featureCard}>
              <View style={styles.featureIconContainer}>
                <Text style={styles.featureIcon}>⚡</Text>
              </View>
              <Text style={styles.featureTitle}>Fast</Text>
              <Text style={styles.featureDesc}>Quick and accurate medical information</Text>
            </View>
            <View style={styles.featureCard}>
              <View style={styles.featureIconContainer}>
                <Text style={styles.featureIcon}>🔒</Text>
              </View>
              <Text style={styles.featureTitle}>Secure</Text>
              <Text style={styles.featureDesc}>Your healthcare data is protected</Text>
            </View>
          </View>

          <TouchableOpacity
            style={styles.startButton}
            onPress={() => navigation.navigate('Chat')}
            activeOpacity={0.8}
          >
            <View style={styles.buttonContent}>
              <Text style={styles.buttonText}>Start Consultation</Text>
              <Text style={styles.buttonArrow}>▶</Text>
            </View>
          </TouchableOpacity>
        </Animatable.View>
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 50,
  },
  settingsButton: {
    position: 'absolute',
    top: 50,
    right: spacing.md,
    zIndex: 1,
  },
  settingsIcon: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  settingsText: {
    fontSize: 18,
    color: colors.text.primary,
  },
  header: {
    alignItems: 'center',
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.md,
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: spacing.xl,
  },
  avatarContainer: {
    marginBottom: spacing.lg,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 3,
    borderColor: colors.surface,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 8,
  },
  welcomeText: {
    fontSize: typography.sizes.sm,
    color: colors.text.secondary,
    fontWeight: '500',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: spacing.xs,
  },
  userName: {
    fontSize: typography.sizes.xl,
    color: colors.text.primary,
    fontWeight: typography.weights.bold,
    marginBottom: spacing.sm,
  },
  subtitle: {
    fontSize: typography.sizes.md,
    color: colors.text.secondary,
    textAlign: 'center',
    maxWidth: 280,
    lineHeight: 22,
  },
  content: {
    paddingHorizontal: spacing.md,
  },
  featuresContainer: {
    flexDirection: width < 380 ? 'column' : 'row',
    justifyContent: width < 380 ? 'center' : 'space-between',
    alignItems: width < 380 ? 'center' : 'stretch',
    marginBottom: spacing.lg,
    paddingHorizontal: spacing.xs,
  },
  featureCard: {
    flex: width < 380 ? 0 : 1,
    width: width < 380 ? '90%' : undefined,
    maxWidth: width < 380 ? 300 : undefined,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.sm,
    alignItems: 'center',
    marginHorizontal: width < 380 ? 0 : spacing.xs,
    marginVertical: width < 380 ? spacing.xs : 0,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  featureIconContainer: {
    width: 48,
    height: 48,
    borderRadius: borderRadius.md,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  featureIcon: {
    fontSize: 20,
    fontWeight: typography.weights.bold,
    color: colors.text.primary,
  },
  featureTitle: {
    fontSize: typography.sizes.sm,
    color: colors.text.primary,
    fontWeight: typography.weights.semibold,
    marginBottom: spacing.xs,
    textAlign: 'center',
  },
  featureDesc: {
    fontSize: typography.sizes.xs,
    color: colors.text.secondary,
    textAlign: 'center',
    lineHeight: 16,
  },
  startButton: {
    marginBottom: spacing.xl,
    marginHorizontal: spacing.sm,
  },
  buttonContent: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 6,
  },
  buttonText: {
    fontSize: typography.sizes.md,
    color: colors.text.primary,
    fontWeight: typography.weights.semibold,
    marginRight: spacing.sm,
  },
  buttonArrow: {
    fontSize: typography.sizes.lg,
    color: colors.text.secondary,
    fontWeight: typography.weights.bold,
  },
});

export default HomeScreen;