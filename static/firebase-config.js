import {initializeApp} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import {
	getAuth,
	GoogleAuthProvider,
	OAuthProvider,
} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import {
	getFirestore
} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-firestore.js";



//firebase configuration for app
const firebaseConfig = {
	apiKey: "AIzaSyCGs8OWbfP-A-8YgHEHnGKbM8TkIoNXRSM",
	authDomain: "dbowy-8aa9c.firebaseapp.com",
	projectId: "dbowy-8aa9c",
	storageBucket: "dbowy-8aa9c.firebasestorage.app",
	messagingSenderId: "615754388073",
	appId: "1:615754388073:web:135ca64fe7578e10d088f8",
	measurementId: "G-QTQBNY34XR"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

const googleProvider = new GoogleAuthProvider();
const appleProvider = new OAuthProvider("apple.com");

const db = getFirestore(app);

export { auth, googleProvider, appleProvider, db };
   
