import { auth } from "./firebase-config.js";
import {
	signInWithEmailAndPassword,
	createUserWithEmailAndPassword,
	GoogleAuthProvider,
	OAuthProvider,
	signInWithPopup,
	sendPasswordResetEmail
} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import { 
	signInWithRedirect,
	getRedirectResult
} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";

const googleProvider = new GoogleAuthProvider();
const appleProvider = new OAuthProvider('apple.com');

const emailInputEl = document.getElementById("email-input");
const passwordInputEl = document.getElementById("password-input");
const signInButtonEl = document.getElementById("sign-in-btn");
const createAccountButtonEl = document.getElementById("create-account-btn");
const signInWithGoogleButtonEl = document.getElementById("sign-in-with-google-btn");
const signUpWithGoogleButtonEl = document.getElementById("sign-up-with-google-btn");
const signInWithAppleButtonEl = document.getElementById("sign-in-with-apple-btn");
const signUpWithAppleButtonEl = document.getElementById("sign-up-with-apple-btn");
const forgotPasswordButtonEl = document.getElementById("forgot-password-btn");
const emailForgotPasswordEl = document.getElementById("email-forgot-password");

const errorMsgEmail = document.getElementById("email-error-message");
const errorMsgPassword = document.getElementById("password-error-message");
const errorMsgGoogleSignIn = document.getElementById("google-signin-error-message");
const errorMsgAppleSignIn = document.getElementById("apple-signin-error-message");

if (signInButtonEl) signInButtonEl.addEventListener("click", authSignInWithEmail);
if (createAccountButtonEl) createAccountButtonEl.addEventListener("click", authCreateAccountWithEmail);
if (signInWithGoogleButtonEl) signInWithGoogleButtonEl.addEventListener("click", authSignInWithGoogle);
if (signUpWithGoogleButtonEl) signUpWithGoogleButtonEl.addEventListener("click", authSignUpWithGoogle);
if (signInWithAppleButtonEl) signInWithAppleButtonEl.addEventListener("click", authSignInWithApple);
if (signUpWithAppleButtonEl) signUpWithAppleButtonEl.addEventListener("click", authSignUpWithApple);
if (forgotPasswordButtonEl) forgotPasswordButtonEl.addEventListener("click", resetPassword);

/* == Functions == */

async function authSignInWithEmail() {
	const email = emailInputEl.value;
	const password = passwordInputEl.value;

	try {
		const userCredential = await signInWithEmailAndPassword(auth, email, password);
		const user = userCredential.user;
		const idToken = await user.getIdToken();

		clearAuthFields();

		loginUser(idToken);
	} catch (error) {
	handleAuthError(error, "email");
	}
}

async function authCreateAccountWithEmail() {
	const email = emailInputEl.value;
	const password = passwordInputEl.value;

	console.log("Attempting to create user with:", email, password);

	try {
		const userCredential = await createUserWithEmailAndPassword(auth, email, password);
		const user = userCredential.user;
		const idToken = await user.getIdToken();

		clearAuthFields();

		loginUser(idToken);
	} catch (error) {
		handleAuthError(error, "email");
	}
}


async function authSignInWithGoogle() {
	googleProvider.setCustomParameters({ prompt: "select_account" });
	try {
		await signInWithRedirect(auth, googleProvider);
	} catch (error) {
		console.error("Redirect Error:", error.message);
	}
}

getRedirectResult(auth)
.then((result) => {
	if (result) {
		const user = result.user;
		user.getIdToken().then(idToken => loginUser(idToken));
	}
}).catch((error) => {
	console.error("Result Error:", error.message);
});


async function authSignUpWithGoogle() {
	await authSignInWithGoogle();
}


async function authSignInWithApple() {
	appleProvider.setCustomParameters({ prompt: "select_account" });
	try {
		await signInWithRedirect(auth, appleProvider);
	} catch (error) {
		console.error("Redirect Error:", error.message);
	}
}

getRedirectResult(auth)
.then((result) => {
	if (result) {
		const user = result.user;
		user.getIdToken().then(idToken => loginUser(idToken));
	}
}).catch((error) => {
	console.error("Result Error:", error.message);
});


async function authSignUpWithApple() {
	await authSignInWithApple();
}


async function resetPassword() {
	const email = emailForgotPasswordEl.value;
	clearInputField(emailForgotPasswordEl);

	try {
		await sendPasswordResetEmail(auth, email);
		document.getElementById("reset-password-view").style.display = "none";
		document.getElementById("reset-password-confirmation-page").style.display = "block";
	} catch (error) {
		console.error("Reset Password Error:", error.message);
		errorMsgEmail.textContent = error.message;
	}
}


function loginUser(idToken) {
	fetch("/auth", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"Authorization": `Bearer ${idToken}`
		},
		credentials: "same-origin"
	})
	.then(response => {
		if (response.ok) {
			window.location.href = "/";
		} else {
			console.error("Failed to login");
		}
	})
	.catch(error => console.error("Fetch Error:", error));
}


function clearInputField(field) {
	field.value = "";
}

function clearAuthFields() {
	clearInputField(emailInputEl);
	clearInputField(passwordInputEl);
}

function handleAuthError(error, type) {
	if (errorMsgEmail) errorMsgEmail.textContent = "";
	if (errorMsgPassword) errorMsgPassword.textContent = "";

	if (type === "email") {
		switch(error.code) {
			case "auth/invalid-email":
				errorMsgEmail.textContent = "Invalid email address";
				break;
			case "auth/email-already-in-use":
				errorMsgEmail.textContent = "This email is already in use.";
				break;
			case "auth/weak-password":
				errorMsgPassword.textContent = "Password must be at least 6 characters.";
				break;
			case "auth/user-not-found":
			case "auth/wrong-password":
			case "auth/invalid-credential":
				errorMsgPassword.textContent = "Invalid email or password.";
				break;
			case "auth/too-many-requests":
				errorMsgPassword.textContent = "Too many attempts. Please try again later.";
				break;
			default:
				console.error(error);
				errorMsgEmail.textContent = "An error occurred (" + error.code + ")";
		}
	}
}
