
Project Title: DataBouy

Video Demo: https://youtu.be/RiOWVUYJXtc

Description:

The Databouy project is a robust web application designed to bridge the gap between students seeking academic assistanceand qualified writers or proofreaders. Built using the Flask framework and powered by Google Firebase, this platform facilitates a complete lifecycle of academic support: from initial quote generation and secure payment to task allocation, document submission, and financial withdrawals.

The primary goal of the project was to create a secure, transparent, and automated ecosystem for academc gig work. Students can browse available tasks, accept them under strict deadlines, and earn a commission. The integration of real-time databases and cloud storage ensures that all academic files and financial records are handled with high integrity.

The project is structured to separate concerns between web routing, external API integrations, and cloud services. Below is a detailed breakdown of the core files:

1. app.py
This is the heart of the application. It initializes the Flask server, configures the session management using the filesytem to ensure persistence, and establishes the connection to Firebase Admin SDK.
- Authentication: it handles user sessions via Google identify tokens and custom login/signup routes.
- Business Logic: it defines the pricing tiers for assignments (e.g., 100 ZMW for under 5 pages, scaling up to 250 ZMW for 15 pages).

2. helpers.py
This file contains utility functions that keep the main application code clean and does not repeat itself.
- Security: includes the @login_required decorator to protect sensitive routes like /profile and /withdraw.
- Payments: houses the logic for initiate_payment and verify_payment, interfacing with providers like MoneyUnify and Paystack.
- Formatting: Contains the zmw filter for currency formatting and phone number normalization logic to ensure consistency across different mobile network input formats.

3. firebase-auth.json & .env
These files (which should be kept out of version control) handle the project's security credentials. The .env file manages environment variables lie SECRET_EY and API keys for payments gateways, while the JSON file provides the service account credentials for Firestore and Cloud Storage access.

During the development of this project, several critical design choices were made to balance user experience with system reliability. One of the most significant debates was whether to use a traditional SQL database (like PostgreSQL) or NoSQL solution like Firestore. I chose Firestore because the data structure for assignments can be hierarchical and varied. For instance, a "quote" might eventually need to store nested arrays of feedback or multiple versions of a file. Firestore's flexible document structure and built-in-real-time capabilities made it superior for a platform where task status updates need to be reflected immediately for writers.

I implemented a fixed commission constant:
- WRITER_COMMISSION = 0.5 (50%)
- PROOFREADER_COMMISSION = 1/6 (16.7%)
This choice was made to ensure the platform remains sustainable. By hardcoding these as constants at the top of app.py, the business logic remains transparent and easy to adjust as the marketplace scales.

I debated between "Automatic Webhooks" and "Manual Polling" for payment verification. Given the constraints of some mobile money APIs in the region, I opted for a hybrid approach. The /payment/verify route allows users to manually trigger a status check if the automated redirect fails, ensuring that no user is stuck in a "pending" state due to a lost session.

Students can visit the /quote page to input their task details. The system calculates a price based on complexity and page count. Once a student pays via mobile money or card, the task is moved into the global pool for writers. The /tasks dashboard serves as a "job board." Writers can see the potential earnings (50% of the total price) before accepting a task. To ensure quality, once a writer submits a file, the status changes to waiting_proofread, allowing a second user to earn a commission by reviewing the work. The /withdraw system is designed with safety checks. It calculates a user's available_balance by summing all approved_work payouts and subtracting any previous withdrawals. This ensures that users can only withdraw funds that have been fully earned and verified by the system.

This project demonstrates a full-stack implamentation of a service-based marketplace. By leveraging Flas for the backend and Firebase for the heavy lifting of data and storage, I have created a scalable application that handles complex user roles, financial transactions, and file management with ease.
