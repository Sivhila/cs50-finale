import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import { 
	getAuth,
	createUserWithEmailAndPassword,
	signOut,
	onAuthStateChanged,
	signInWithPopup,
	GoogleAuthProvider,
	OAuthProvider
} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js



firebaseConfig = {
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




const signOutButtonEl = document.getElementById("sign-out-btn")
signOutButtonEl.addEventListener("click", authSignOut)

const signInWithGoogleButtonEl = document.getElementById("sign-in-with-google-btn")
const signInWithAppleButtonEl = document.getElementById("sign-in-with-apple-btn")

const emailInputEl = document.getElementById("email-input")
const passwordInputEl = document.getElementById("password-input")

const signInButtonEl = document.getElementById("sign-in-btn")



signInWithGoogleButtonEl.addEventListener("click", authSignInWithGoogle)
signInWithAppleButtonEl.addEventListener("click", authSignInWithApple)

signInButtonEl.addEventListener("click", authSignInWithEmail)
createAccountButtonEl.addEventListener("click", authCreateAccountWithEmail)



onAuthStateChanged(auth, (user) => {
	if (user) {
		// https://firebase.google.com/docs/reference/js/auth.user
		const uid = user.uid;
		user.getIdToken().then(function(idToken) {
			console.log(idToken);
		});

		showLoggedInView(user)
	} else {
		showLoggedOutView()
	}
});



function authSignInWithGoogle() {

	signInWithPopup(auth, provider)
	.then((result) => {

		const credential = GoogleAuthProvider.credentialFromResult(result);
		const token = credential.accessToken;

		const user = result.user;
		user.getIdToken().then(function(idToken) {
			console.log(idToken);
		});

		showLoggedInView(user)
	}).catch((error) => {
		const credential = GoogleAuthProvider.credentialFromError(error);

		console.error(error.message)
	});
}



function authSignInWithApple() {
	signInWithPopup(auth, provider)
	.then((result) => {

		const credential = OAuthProvider.credentialFromResult(result);
		const token = credential.accessToken;

		const user = result.user;
		user.getIdToken().then(function(idToken) {
			console.log(idToken);
		});
		showLoggedInView(user)
	}).catch((error) => {
		const credential = OAuthProvider.credentialFromError(error);

		console.error(error.message)
	});
}


function authSignInWithEmail() {
	console.log("Sign in with email and password")

	const email = emailInputEl.value
	const password = passwordInputEl.value

	signInWithEmailAndPassword(auth, email, password)
	.then((userCredential) => {

		const user = userCredential.user;
		console.log("User signed in: ", user)
		clearAuthFields()
	})
	.catch((error) => {
		const errorCode = error.code;
		const errorMessage = error.message;
		console.error("Error signing in: ", errorMessage)
	});
}


function authCreateAccountWithEmail() {

	const email = emailInputEl.value
	const password = passwordInputEl.value

	createUserWithEmailAndPassword(auth, email, password)
	.then((userCredential) => {

		const user = userCredential.user;
		console.log("User created: ", user)
		clearAuthFields()
	})
	.catch((error) => {
		const errorCode = error.code;
		const errorMessage = error.message;
		console.error("Error creating user: ", errorMessage)
	});
}



function authSignOut() {
	console.log("User signed out")
	signOut(auth).then(() => {
		console.log("User signed out")
	}).catch((error) => {
		console.error(error.message)
	});
}



function showLoggedOutView() {
	console.log("Show logged out view")
}



function showLoggedInView(user) {
	console.log("Show logged in view")
	console.log(user.uid)
	window.location.href = "/profile";
}



function clearInputFields() {
	field.value = ""
}




function clearAuthFields() {
	clearInputField(emailInputEl)
	clearInputField(passwordInputEl)
}

