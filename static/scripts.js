document.addEventListener("DOMContentLoaded", function () {

	const roleSelect = document.getElementById("roleSelect");
	const certificateSection = document.getElementById("certificate-section");

	if (roleSelect && certificateSection) {
		function toggleCertificate() {
			certificateSection.style.display =
				roleSelect.value === "writer" ? "block" : "none";
		}

		toggleCertificate();
		roleSelect.addEventListener("change", toggleCertificate);
		console.log("Profile JS loaded");
	}

	
	const researchRadio = document.getElementById("research");
	const assignmentRadio = document.getElementById("assignment");
	const researchTeam = document.getElementById("researchTeam");

	if (researchRadio && assignmentRadio && researchTeam) {
		researchRadio.addEventListener("change", () => {
			researchTeam.style.display = "block";
		});

		assignmentRadio.addEventListener("change", () => {
			researchTeam.style.display = "none";
		});
	}


	const paymentMethod = document.getElementById("paymentMethod");
	const mobileMoneySection = document.getElementById("mobileMoneySection");
	const cardSection = document.getElementById("cardSection");

	if (paymentMethod && mobileMoneySection && cardSection) {
		paymentMethod.addEventListener("change", function () {
			if (this.value === "mobile") {
				mobileMoneySection.style.display = "block";
				cardSection.style.display = "none";
			} else if (this.value === "card") {
				cardSection.style.display = "block";
				mobileMoneySection.style.display = "none";
			} else {
				mobileMoneySection.style.display = "none";
				cardSection.style.display = "none";
			}
		});
	}



	const countdownEl = document.getElementById("countdown");
	const submitBtn = document.getElementById("submitBtn");

	if (countdownEl) {
		let remainingSeconds = parseInt(countdownEl.dataset.seconds, 10) || 0;

		const timer = setInterval(() => {
			if (remainingSeconds <= 0) {
				clearInterval(timer);
				countdownEl.textContent = "Time Expired";
				if (submitBtn) submitBtn.disabled = true;
				return;
			}

			countdownEl.textContent = formatTime(remainingSeconds);
			remainingSeconds--;
		}, 1000);
	}


	const withdrawMethod = document.getElementById("withdraw_method");

	if (withdrawMethod) {
		withdrawMethod.addEventListener("change", function () {
			document.getElementById("mobile").style.display =
				this.value === "mobile" ? "block" : "none";
			document.getElementById("card").style.display =
				this.value === "card" ? "block" : "none";
		});
	}
});


function formatTime(seconds) {
	const hrs = Math.floor(seconds / 3600);
	const mins = Math.floor((seconds % 3600) /60);
	const secs = seconds % 60;
	return `${hrs}h ${mins}m ${secs}s`;
}


