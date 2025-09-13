import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';

const { width, height } = Dimensions.get('window');

const SplashScreen = () => {
  return (
    <LinearGradient
      colors={['#6366f1', '#8b5cf6', '#a855f7']}
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
          <Text style={styles.logo}>💬</Text>
        </Animatable.View>
        <Animatable.Text 
          animation="fadeIn"
          delay={500}
          style={styles.title}
        >
          RAG Chat Assistant
        </Animatable.Text>
        <Animatable.Text 
          animation="fadeIn"
          delay={800}
          style={styles.subtitle}
        >
          Intelligent Conversations Powered by AI
        </Animatable.Text>
      </Animatable.View>
      <Animatable.View 
        animation="fadeIn"
        delay={1200}
        style={styles.footer}
      >
        <View style={styles.loadingDots}>
          <Animatable.View 
            animation="bounce" 
            iterationCount="infinite"
            delay={0}
            style={[styles.dot, { backgroundColor: '#fff' }]} 
          />
          <Animatable.View 
            animation="bounce" 
            iterationCount="infinite"
            delay={200}
            style={[styles.dot, { backgroundColor: '#fff' }]} 
          />
          <Animatable.View 
            animation="bounce" 
            iterationCount="infinite"
            delay={400}
            style={[styles.dot, { backgroundColor: '#fff' }]} 
          />
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
  },
  logoContainer: {
    width: 120,
    height: 120,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
  },
  logo: {
    fontSize: 60,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  footer: {
    position: 'absolute',
    bottom: 60,
  },
  loadingDots: {
    flexDirection: 'row',
    gap: 8,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
});

export default SplashScreen;
