import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  signOut,
  sendPasswordResetEmail,
  onAuthStateChanged,
  updateProfile
} from 'firebase/auth';
import { auth, googleProvider, isFirebaseConfigured } from '../firebase';

const AuthContext = createContext(null);

function logFirebaseDiagnostic(action, err) {
  console.error(`[Firebase Auth Diagnostic - ${action}]`, {
    code: err?.code,
    message: err?.message,
    apiKeyConfigured: isFirebaseConfigured(),
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'MISSING',
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'MISSING',
    appId: import.meta.env.VITE_FIREBASE_APP_ID ? 'LOADED' : 'MISSING',
    timestamp: new Date().toISOString()
  });
}

function getFriendlyErrorMessage(err) {
  if (!err) return "Authentication error occurred.";
  const code = err.code || "";
  const msg = err.message || "";

  if (code === 'auth/configuration-not-found' || code === 'auth/operation-not-allowed') {
    return "Google Sign-In is not enabled in your Firebase Console. Go to Firebase Console -> Authentication -> Sign-in method, edit Google provider, select support email, and click Save.";
  }
  if (code === 'auth/api-key-not-valid' || code === 'auth/invalid-api-key' || msg.includes('api-key')) {
    return "Firebase API Key is invalid or uninitialized. Please verify VITE_FIREBASE_API_KEY in frontend/.env.";
  }
  if (code === 'auth/popup-closed-by-user') {
    return "Google Sign-In popup was closed before completing authentication.";
  }
  if (code === 'auth/popup-blocked') {
    return "Google Sign-In popup was blocked by your browser. Falling back to redirect...";
  }
  if (code === 'auth/cancelled-popup-request') {
    return "Sign-In request was cancelled. Please try again.";
  }
  if (code === 'auth/unauthorized-domain') {
    return "Domain (localhost) is not authorized in Firebase Console under Authentication -> Settings -> Authorized domains.";
  }
  if (code === 'auth/internal-error') {
    return "Firebase internal authentication error. Please check your network and project settings.";
  }
  if (code === 'auth/account-exists-with-different-credential') {
    return "An account already exists with the same email address using a different sign-in method.";
  }
  if (code === 'auth/invalid-credential' || code === 'auth/wrong-password') {
    return "Invalid email address or password.";
  }
  if (code === 'auth/user-not-found') {
    return "No user account found with this email address.";
  }
  if (code === 'auth/email-already-in-use') {
    return "An account with this email address already exists.";
  }
  if (code === 'auth/weak-password') {
    return "Password is too weak. Please use at least 6 characters.";
  }
  if (code === 'auth/network-request-failed') {
    return "Network connection error. Please check your internet connection.";
  }

  return msg.replace(/^Firebase:\s*/, '').replace(/auth\//g, '') || "Authentication failed. Please try again.";
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('rag_auth_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => {
    return localStorage.getItem('rag_auth_token') || null;
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let unsubscribe = () => {};

    if (auth && isFirebaseConfigured()) {
      // Check for redirect result if popup fell back to redirect
      getRedirectResult(auth)
        .then(async (result) => {
          if (result?.user) {
            const firebaseUser = result.user;
            const idToken = await firebaseUser.getIdToken();
            const displayName = firebaseUser.displayName || firebaseUser.email?.split('@')[0] || 'Researcher';
            const userObj = {
              id: firebaseUser.uid,
              name: displayName,
              email: firebaseUser.email,
              avatarUrl: firebaseUser.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&background=18181b&color=ffffff`,
              emailVerified: firebaseUser.emailVerified,
            };
            setUser(userObj);
            setToken(idToken);
            localStorage.setItem('rag_auth_user', JSON.stringify(userObj));
            localStorage.setItem('rag_auth_token', idToken);
          }
        })
        .catch((err) => {
          logFirebaseDiagnostic('getRedirectResult', err);
        });

      try {
        unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
          if (firebaseUser) {
            try {
              const idToken = await firebaseUser.getIdToken();
              const displayName = firebaseUser.displayName || firebaseUser.email?.split('@')[0] || 'Researcher';
              const userObj = {
                id: firebaseUser.uid,
                name: displayName,
                email: firebaseUser.email,
                avatarUrl: firebaseUser.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&background=18181b&color=ffffff`,
                emailVerified: firebaseUser.emailVerified,
              };
              setUser(userObj);
              setToken(idToken);
              localStorage.setItem('rag_auth_user', JSON.stringify(userObj));
              localStorage.setItem('rag_auth_token', idToken);
            } catch (err) {
              logFirebaseDiagnostic('getIdToken', err);
            }
          } else {
            setUser(null);
            setToken(null);
            localStorage.removeItem('rag_auth_user');
            localStorage.removeItem('rag_auth_token');
          }
          setLoading(false);
        });
      } catch (err) {
        logFirebaseDiagnostic('onAuthStateChanged', err);
        setLoading(false);
      }
    } else {
      setLoading(false);
    }

    return () => unsubscribe();
  }, []);

  const login = async (email, password, remember = true) => {
    setLoading(true);

    if (!auth || !isFirebaseConfigured()) {
      setLoading(false);
      const err = new Error("Firebase configuration is missing or invalid. Please check frontend/.env.");
      logFirebaseDiagnostic('login', err);
      throw err;
    }

    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const firebaseUser = userCredential.user;
      const idToken = await firebaseUser.getIdToken();
      const displayName = firebaseUser.displayName || firebaseUser.email?.split('@')[0] || 'Researcher';

      const userObj = {
        id: firebaseUser.uid,
        name: displayName,
        email: firebaseUser.email,
        avatarUrl: firebaseUser.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&background=18181b&color=ffffff`,
        emailVerified: firebaseUser.emailVerified,
      };

      setUser(userObj);
      setToken(idToken);
      localStorage.setItem('rag_auth_user', JSON.stringify(userObj));
      localStorage.setItem('rag_auth_token', idToken);
      setLoading(false);
      return { success: true, user: userObj };
    } catch (err) {
      setLoading(false);
      logFirebaseDiagnostic('signInWithEmailAndPassword', err);
      throw new Error(getFriendlyErrorMessage(err));
    }
  };

  const loginWithGoogle = async () => {
    setLoading(true);

    if (!auth || !googleProvider || !isFirebaseConfigured()) {
      setLoading(false);
      const err = new Error("Firebase project configuration is missing or invalid. Please check frontend/.env.");
      logFirebaseDiagnostic('loginWithGoogle', err);
      throw err;
    }

    try {
      googleProvider.setCustomParameters({
        prompt: 'select_account'
      });

      const result = await signInWithPopup(auth, googleProvider);
      const firebaseUser = result.user;
      const idToken = await firebaseUser.getIdToken();

      const displayName = firebaseUser.displayName || firebaseUser.email?.split('@')[0] || 'Researcher';
      const userObj = {
        id: firebaseUser.uid,
        name: displayName,
        email: firebaseUser.email,
        avatarUrl: firebaseUser.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&background=18181b&color=ffffff`,
        emailVerified: firebaseUser.emailVerified,
      };

      setUser(userObj);
      setToken(idToken);
      localStorage.setItem('rag_auth_user', JSON.stringify(userObj));
      localStorage.setItem('rag_auth_token', idToken);
      setLoading(false);
      return { success: true, user: userObj };
    } catch (err) {
      logFirebaseDiagnostic('signInWithPopup', err);

      // Gracefully fall back to signInWithRedirect if popup is blocked
      if (err.code === 'auth/popup-blocked' || err.code === 'auth/cancelled-popup-request') {
        try {
          console.warn("Popup blocked or cancelled. Attempting Google signInWithRedirect fallback...");
          await signInWithRedirect(auth, googleProvider);
          return;
        } catch (redirectErr) {
          setLoading(false);
          logFirebaseDiagnostic('signInWithRedirect', redirectErr);
          throw new Error(getFriendlyErrorMessage(redirectErr));
        }
      }

      setLoading(false);
      throw new Error(getFriendlyErrorMessage(err));
    }
  };

  const signup = async (fullName, email, password) => {
    setLoading(true);

    if (!auth || !isFirebaseConfigured()) {
      setLoading(false);
      const err = new Error("Firebase configuration is missing or invalid. Please check frontend/.env.");
      logFirebaseDiagnostic('signup', err);
      throw err;
    }

    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const firebaseUser = userCredential.user;

      if (fullName) {
        await updateProfile(firebaseUser, { displayName: fullName });
      }

      const idToken = await firebaseUser.getIdToken();
      const displayName = fullName || firebaseUser.email?.split('@')[0] || 'Researcher';
      const userObj = {
        id: firebaseUser.uid,
        name: displayName,
        email: firebaseUser.email,
        avatarUrl: firebaseUser.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&background=18181b&color=ffffff`,
        emailVerified: firebaseUser.emailVerified,
      };

      setUser(userObj);
      setToken(idToken);
      localStorage.setItem('rag_auth_user', JSON.stringify(userObj));
      localStorage.setItem('rag_auth_token', idToken);
      setLoading(false);
      return { success: true, user: userObj };
    } catch (err) {
      setLoading(false);
      logFirebaseDiagnostic('createUserWithEmailAndPassword', err);
      throw new Error(getFriendlyErrorMessage(err));
    }
  };

  const resetPassword = async (email) => {
    if (!auth || !isFirebaseConfigured()) {
      const err = new Error("Firebase configuration is missing or invalid. Please check frontend/.env.");
      logFirebaseDiagnostic('resetPassword', err);
      throw err;
    }

    try {
      await sendPasswordResetEmail(auth, email);
      return { success: true };
    } catch (err) {
      logFirebaseDiagnostic('sendPasswordResetEmail', err);
      throw new Error(getFriendlyErrorMessage(err));
    }
  };

  const logout = async () => {
    if (auth) {
      try {
        await signOut(auth);
      } catch (err) {
        logFirebaseDiagnostic('signOut', err);
      }
    }
    setUser(null);
    setToken(null);
    localStorage.removeItem('rag_auth_user');
    localStorage.removeItem('rag_auth_token');
  };

  const value = {
    user,
    token,
    isAuthenticated: !!user,
    loading,
    login,
    loginWithGoogle,
    signup,
    resetPassword,
    logout,
    isFirebaseConfigured: isFirebaseConfigured(),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
