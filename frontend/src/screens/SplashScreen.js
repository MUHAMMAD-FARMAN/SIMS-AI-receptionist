import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import { colors, typography, spacing, borderRadius } from '../styles/theme';

const { width, height } = Dimensions.get('window');

const SplashScreen = () => {
  return (
    <LinearGradient
      colors={colors.gradient.dark}
      style={styles.container}
    >
      <Animatable.View 
        animation="fadeInUp" 
        duration={1000}
        style={styles.content}
      >
        <Animatable.View 
          animation="pulse" 
          easing="ease-out" 
          iterationCount="infinite"
          style={styles.logoContainer}
        >
          <View style={styles.logoIcon}>
            <Text style={styles.logo}>AI</Text>
          </View>
        </Animatable.View>
        <Animatable.Text 
          animation="fadeIn"
          delay={500}
          style={styles.title}
        >
          SIMS AI Receptionist
        </Animatable.Text>
        <Animatable.Text 
          animation="fadeIn"
          delay={800}
          style={styles.subtitle}
        >
          Intelligent Healthcare Assistant
        </Animatable.Text>
      </Animatable.View>
      
      <Animatable.View 
        animation="fadeIn"
        delay={1200}
        style={styles.footer}
      >
        <View style={styles.loadingContainer}>
          <View style={styles.loadingBar}>
            <Animatable.View 
              animation="pulse"
              iterationCount="infinite"
              style={styles.loadingProgress}
            />
          </View>
          <Text style={styles.loadingText}>Initializing...</Text>
        </View>
      </Animatable.View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
  },
  logoContainer: {
    marginBottom: spacing.xl * 2,
  },
  logoIcon: {
    width: 120,
    height: 120,
    borderRadius: borderRadius.xl,
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.border,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.2,
    shadowRadius: 16,
    elevation: 10,
  },
  logo: {
    fontSize: 48,
    fontWeight: typography.weights.bold,
    color: colors.text.primary,
    letterSpacing: 2,
  },
  title: {
    fontSize: typography.sizes.xxl,
    fontWeight: typography.weights.bold,
    color: colors.text.primary,
    marginBottom: spacing.sm,
    textAlign: 'center',
    letterSpacing: 0.5,
  },
  subtitle: {
    fontSize: typography.sizes.md,
    color: colors.text.secondary,
    textAlign: 'center',
    paddingHorizontal: spacing.xl,
    lineHeight: 22,
  },
  footer: {
    position: 'absolute',
    bottom: spacing.xl * 3,
    alignItems: 'center',
  },
  loadingContainer: {
    alignItems: 'center',
  },
  loadingBar: {
    width: 160,
    height: 3,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.md,
    overflow: 'hidden',
  },
  loadingProgress: {
    width: '40%',
    height: '100%',
    backgroundColor: colors.text.secondary,
    borderRadius: borderRadius.sm,
  },
  loadingText: {
    fontSize: typography.sizes.sm,
    color: colors.text.secondary,
    fontWeight: typography.weights.medium,
    letterSpacing: 0.5,
  },
});

export default SplashScreen;