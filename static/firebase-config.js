import {initializeApp} from "https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";
import {
	getAuth,
	GoogleAuthProvider,
	OAuthProvider,
	signInWithPopup
} from "https://www.gstatic.com/firebasejs/11.0.1/firebase-auth.js";
import {
	getFirestore
} from "https://www.gstatic.com/firebasejs/11.0.1/firebase-firestore.js";
import {
	getStorage,
	ref,
	uploadBytes,
	getDownloadURL
} from "https://www.gstatic.com/firebasejs/11.0.1/firebase-storage.js";


//firebase configuration for app
const firebaseConfig = {
	apiKey: "AIzaSyCGs8OWbfP-A-8YgHEHnGKbM8TkIoNXRSM",
	authDomain: "dbowy-8aa9c.firebaseapp.com",
	projectId: "dbowy-8aa9c",
	storageBucket: "dbowy-8aa9c.appspot.com",
	messagingSenderId: "615754388073",
	appId: "1:615754388073:web:135ca64fe7578e10d088f8",
	measurementId: "G-QTQBNY34XR"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();
const provider = new OAuthProvider(apple.com);
const db = getFirestore();
const storage = getStorage();

export { auth, provider, db};
   
