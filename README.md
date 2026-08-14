WhatsApp Support Bot 
An AI-powered customer support system that provides automatic responses through WhatsApp using the UltraMsg API and AI-based semantic matching. Users can ask questions on WhatsApp, and the system finds the most relevant answers from uploaded FAQ documents. Built with Python, Flask, SQLite, and Sentence Transformers.
Key features
. WhatsApp integration using UltraMsg API
. AI-powered responses using Sentence Transformers
. FAQ document support for PDF, TXT, and DOCX
. Smart FAQ matching to find the most relevant answer
. Conversation history stored in SQLite
. File validation before document processing
. Automatic responses to customer questions
. Simple setup and easy-to-use architecture
Tech stack
. Backend: Python, Flask
. Database: SQLite
. NLP / AI: Sentence Transformers, scikit-learn
. WhatsApp API: UltraMsg
. File parsing: PyPDF2, pdfplumber, python-docx
. Configuration: Python-dotenv
. HTTP Requests: Requests

Project structure

whatsapp-support-bot/
│
├── app.py                  
├── config.py              
├── database.py           
├── rag_engine.py          
├── whatsapp_handler.py   
├── admin_routes.py      
│
├── requirements.txt       
├── .env                   
├── README.md              
│
├── data/
│   ├── faqs/             
│   │   └── sample_faq.txt
│   └── chroma.db/       
│
├── templates/
│   └── admin.html       
│
└── uploads/              

Prerequisites
. Python (3.8+)
. UltraMsg account
. Ngrok
. WhatsApp number connected with UltraMsg
Backend (Flask API)
pip install -r requirements.txt
python app.py

Server runs at:
http://localhost:5000

WhatsApp setup
. Create and configure an UltraMsg account
. Connect your WhatsApp number with UltraMsg
. Start the Flask application
. Run Ngrok on port 5000
. Copy the generated Ngrok URL
. Add the Ngrok URL as the webhook URL in the UltraMsg dashboard
. Make sure the webhook URL ends with /webhook
. Enable webhook receiving in UltraMsg
Adding FAQ documents
. Create the data/faqs folder
. Add FAQ documents in PDF, TXT, or DOCX format
. Include information about products, services, account issues, business hours, and customer support questions
. The AI system processes these documents and uses them to answer customer queries
How to use
. Send a message to the connected WhatsApp number
. UltraMsg forwards the incoming message to the Flask webhook
. The system processes the user's question
. Sentence Transformers compare the question with available FAQ information
. The most relevant answer is selected
. The response is sent back through WhatsApp
. The conversation is saved in the SQLite database
Example conversation
. User: How do I reset my password?
. Bot: To reset your password, go to the login page, select Forgot Password, enter your registered email, and follow the reset instructions.
. User: What are your business hours?
. Bot: Our business hours are Monday to Friday from 9 AM to 6 PM.
. User: Hello
. Bot: Welcome. How can I help you today?
API endpoints
. Webhook: Receives incoming WhatsApp messages
. Send Message: Sends responses to WhatsApp through the UltraMsg API
Testing notes
. Greeting test → Send Hello and verify the welcome response
. FAQ test → Ask a question related to the uploaded FAQ documents
. Unknown question test → Ask an unrelated question and verify that the bot requests clarification
. File test → Upload valid and invalid FAQ file types and verify validation
. Database test → Check SQLite for stored conversation history
. Webhook test → Send a WhatsApp message and verify that the Flask webhook receives it
Troubleshooting
. Webhook not receiving messages: Check that Ngrok is running and the correct /webhook URL is configured in UltraMsg
. Messages not sending: Verify the UltraMsg instance ID and token in the .env file
. No bot response: Make sure FAQ documents exist in data/faqs
. Incorrect answers: Check that the FAQ documents contain sufficient and relevant information
. File processing errors: Verify that uploaded PDF, TXT, or DOCX files are valid and not corrupted
. Database issues: Make sure the application has permission to create and access the SQLite database
Project purpose
To provide fast, simple, and intelligent customer support through WhatsApp by combining automated messaging, AI-powered FAQ matching, and conversation history management.
