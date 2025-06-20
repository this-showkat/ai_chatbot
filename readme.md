## AI Integrated Chatbot Project

Hi! I have created an AI integrated chatbot backend that lets users connect and have real time conversation with the chatbot for free.  All you need to get access is to create an account to the portal using your active email.

## Technology Stack

 - `OpenRouter AI` as AI Gateway platform and `deepseek/deepseek-r1:free` as the LLM. 
 - `Python` as programming language, `Django` as the framework and `Django Rest Framework` for API development, 
 - `Django Channels` package for **web socket** programming (real conversation).
 - `PostgreSQL` database engine to store into and retrieve data
 - `drf simple_jwt` for **JWT** base authentication.
 - `SMTP` (of gmail) for email verification.
 - and more ..
 

## Key Features Implemented

 - **User Authentication:** Users can create an account, Login,  view their profile, reset password, update password using their active email with Email verification OTP.
 - **AI Chat Bot:** Logged in users can have real time conversation through the web socket api. 
 - **View Conversation History:**  The Conversations between user and AI agent are stored in the database, so an user can later see their own conversation. 
 - and more ..
 
## Key APIs (Web Socket, for localhost)
- **Real Time Conversation API:** ws://localhost:8000/ws/chat/?token={{ACCESS_TOKEN}}
(to connect to the AI chatbot, json formatted query data needs to be sent, `{'message': '<Your message here>', conversation_id: <conversation-id/null>}` if conversation id is null, then new conversation will be created. Created Conversations can be retrieved through HTTP/HTTPS APIs.


## Key APIs (HTTP/HTTPS, for localhost)
BASE_URL = http://localhost:8000/api/v1 for localhost
- **To Login**:  `POST: {{BASE_URL}}/auth/login/` with username, and password.
- **To Register**: Register needs 3 step actions: (1) First, get OTP via email, (2) Verify the OTP, (3) Now complete with other basic info to create account.
- **Note: Postman API  Collection files has been attached with the project in the  `API_Collections` directory. which could be imported into Postman.** 




## How to Run the the Project

To Run the project (assuming on development server), Simply clone the project source code into your computer, create a python virtual environment and activate it, then install the required packages using `pip install -r requirements.txt`,. I have exposed the `.env.backup` with some real password too, you need to rename the file into `.env` and then since we are working with async functionality, we need to start the project using `python manage.py runserver` (We are using `daphne` server to run the project on asgi.py.  and then open the postman, import the postman api collections (available in the `API Collection` directory of this project) and go to the `auth` folder, create an account, then login, and then then go to the Websocket api to initiate conversation with the AI Chatbot.


## Thank you for reading with patient

The project was interesting. This was the very first time for me to get engaged with AI as a worker, (not just user! ),  and only half of a day I could  work on the AI part. I have worked on some other features partially. I wish i could make it more realistic! Thank you #BDCalling for having me the opportunity to let me work on this project. Special thanks goes to Pritom Banerjee, Team Lead, SparkTech, Paritosh (friend), and you, who are reading this with patient.
