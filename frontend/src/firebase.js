import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const apiKey = import.meta.env.VITE_FIREBASE_API_KEY || '';

const firebaseConfig = {
  apiKey: apiKey,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || '',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || ''
};

export function isFirebaseConfigured() {
  const key = import.meta.env.VITE_FIREBASE_API_KEY;
  return Boolean(key && key.trim() !== '' && key !== 'demo-api-key' && key !== 'YOUR_FIREBASE_API_KEY');
}

let appInstance = null;
let authInstance = null;
let googleProviderInstance = null;

if (isFirebaseConfigured()) {
  try {
    appInstance = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
    authInstance = getAuth(appInstance);
    googleProviderInstance = new GoogleAuthProvider();
    googleProviderInstance.setCustomParameters({
      prompt: 'select_account'
    });
  } catch (err) {
    console.warn("Firebase Auth initialization error:", err.message);
  }
}

export const app = appInstance;
export const auth = authInstance;
export const googleProvider = googleProviderInstance;
