import { initializeApp } from "firebase/app";
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  FacebookAuthProvider,
  TwitterAuthProvider,
  signInWithPopup,
  updateProfile,
  signOut,
} from "firebase/auth";

// Values can be overridden via env to match the exact Firebase project.
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY || "AIzaSyA61zVuk4rUf3L4fGAuKgfkwvmZQOJXeFk",
  authDomain:
    process.env.REACT_APP_FIREBASE_AUTH_DOMAIN || "thee-boggle-boost-4ec28.firebaseapp.com",
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID || "thee-boggle-boost-4ec28",
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET || "thee-boggle-boost-4ec28.appspot.com",
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || "191458719746",
  appId: process.env.REACT_APP_FIREBASE_APP_ID || "1:191458719746:web:9bb860e4ba783e6bc68f1b",
  measurementId: process.env.REACT_APP_FIREBASE_MEASUREMENT_ID || "G-FBQP33Z1LP",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

async function getFreshIdToken(cred) {
  const user = cred?.user;
  if (!user) {
    throw new Error("Missing user from Firebase credential.");
  }
  return user.getIdToken(true);
}

export async function signupWithEmailPassword(email, password, displayName) {
  const cred = await createUserWithEmailAndPassword(auth, email, password);
  if (displayName) {
    await updateProfile(cred.user, { displayName });
  }
  return getFreshIdToken(cred);
}

export async function loginWithEmailPassword(email, password) {
  const cred = await signInWithEmailAndPassword(auth, email, password);
  return getFreshIdToken(cred);
}

export async function loginWithGoogle() {
  const provider = new GoogleAuthProvider();
  const cred = await signInWithPopup(auth, provider);
  return getFreshIdToken(cred);
}

export async function loginWithFacebook() {
  const provider = new FacebookAuthProvider();
  const cred = await signInWithPopup(auth, provider);
  return getFreshIdToken(cred);
}

export async function loginWithTwitter() {
  const provider = new TwitterAuthProvider();
  const cred = await signInWithPopup(auth, provider);
  return getFreshIdToken(cred);
}

export async function logoutFirebase() {
  await signOut(auth);
}
