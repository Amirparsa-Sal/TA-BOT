# TA BOT

This project is an open source Telegram bot which can be used as a teaching assistant bot if you are trying to find an easy and secure way to communicate with your students.

<a target="_blank" href="https://github.com/yurijserrano/LANGUAGES-TOOLS-LOGOS">
	<img src="https://img.shields.io/badge/Python-blue?style=for-the-badge&color=094e87" />
	<img src="https://github.com/yurijserrano/Github-Profile-Readme-Logos/blob/master/programming%20languages/python.svg" width="30" />
</a>&nbsp;
<a target="_blank" href="https://github.com/yurijserrano/LANGUAGES-TOOLS-LOGOS">
	<img src="https://img.shields.io/badge/Django-gray?style=for-the-badge&color=555555" />
	<img src="https://github.com/yurijserrano/Github-Profile-Readme-Logos/blob/master/frameworks/django.svg" width="30" />
</a>&nbsp;
 <a target="_blank" href="https://github.com/yurijserrano/LANGUAGES-TOOLS-LOGOS">
	 <img src="https://img.shields.io/badge/Redis-red?style=for-the-badge&color=FF0000" />
	 <img src="https://github.com/yurijserrano/Github-Profile-Readme-Logos/blob/master/databases/redis.svg" width="30" />
</a>&nbsp;
<a target="_blank" href="https://github.com/yurijserrano/LANGUAGES-TOOLS-LOGOS">
	 <img src="https://img.shields.io/badge/Telegram-blue?style=for-the-badge&color=0088CC" />
	 <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" width="30" />
</a>&nbsp;
<a target="_blank" href="https://github.com/yurijserrano/LANGUAGES-TOOLS-LOGOS">
	 <img src="https://img.shields.io/badge/Docker-blue?style=for-the-badge&color=4990DF" />
	 <img src="https://github.com/yurijserrano/Github-Profile-Readme-Logos/blob/master/cloud/docker.svg" width="30" />
</a>&nbsp;

# Contents
- [Bot Features](#bot-features)
- [Deploying TA BOT](#deploying-ta-bot)
- [Admins Secret Commands](#admins-secret-commands)

# Bot Features

- ### Configurability

  The bot is designed to be configurable. as a result, you can use the bot for your course, no matter in which university and for which course you are trying to use the bot.

  You can edit all of the bot messages if you want them to be changed.

  You can edit all of the bot buttons if you want them to be changed.

  You can use your own email smtp to send one time passwords (OTP) to authenticate users.

  You can use your own email regex to validate users in registeration.

  You can set up the tables related to students data by uploading a csv,xlsx,json,yaml,... in admin panel very easily.

  You can set up a default secret key for the teacher or teaching assistants to access the telegram admin panel.

  You can set up your own course syllabus for categorizing resources and timeline.

- ### Privacy & Security

  Before using the bot, you can upload your students data containing their email, student_id, first name, last name and password to authenticate them. Students then can register using that information. 

  They must send their own email in telegram, then the bot sends a one time password to their email (if they have entered a valid email) and after entering that password, the bot asks them to set their password. After entering the password the registeration is complete.

  Obviously, there is a login section in which the students can login to their account using an email and a password. Each student has its own account and he/she can login to the account with multiple devices at the same time.

- ### Telegram Admin Panel

  There is an admin panel for teachers and teaching assistants in telegram. You can use the admin panel in any private chat or group. The teacher and the teaching assistant team can login to their account using a predefined secret key which you can configure and change it.

  In admin panel, you can access all the bot features such as homeworks, grading, answering questions, sending and receiving notifications and adding some resources for the course. Also there is a full CRUD support for some features like homeworks and grading which you can access all of them in admin panel.

- ### Homeworks & Grading

  You can create new homeworks in admin panel and set a title, due date and a file to that homeworks to be shown to the students. Also, you can hide homeworks until you want them to be published.

  You can set a grade link for each homework which containts a link to grading sheet or something like that.

  Students can access the homeworks and the grading for each homework, in their own account.

- ### Asking & Answering questions

  Students can ask their questions and you can anonymously answer them. 

  The bot will forward the questions to all the chats that have access to admin panel if you have enabled incoming notifications for that chat. This means that you can have a seperate group for answering questions while you have other groups or chats for managing the bot. After answering the question, the bot will forward the answer to the student who had asked the question. 

  Furthermore, you have access to a list of unanswered questions which you may want to answer them later.

- ### Resources

  You can share some resources to students containing a title and a link. The resources are sorted by course syllabus. Students can 		access all resources    related to a specific chapter of a course.

- ### Timeline

  You can set the course timeline so that the students can be informed if a chapter is taught in the class.

- ### Notifications (Available on next update)

  You can send notifications to all students to tell them if they have a new homework or a new grading sheet is uploaded anything else.

# Deploying TA BOT

### Create Your Google SMTP Account and Config the Backend

​	You follow this [guide](https://www.hostinger.com/tutorials/how-to-use-free-google-smtp-server) to create your Google SMTP account.

### Set Environment Varibales
In the root directory of the project create a `.env` file:

```bash
touch .env
```

You must specify the following items:

```bash
SERVER_DOMAIN=your_domain #Domain of your server. Used to access django admin panel.

POSTGRES_DB=you_db_name # The postgres DB you want to create
POSTGRES_USER=your_postgres_user # The postgres user you want to create
POSTGRES_PASSWORD=your_postgres_password # The password for postgres user

EMAIL_HOST=smtp.gmail.com #Your SMTP host
EMAIL_SENDER=example@gmail.com #Your SMTP account email
EMAIL_PASSWORD=your_password #Your SMTP account password
EMAIL_PORT=465 # SMTP Port

SECRET_KEY=example_secret #Secret key for bot admins (must be strong enough)

DJANGO_SUPERUSER_EMAIL=example@gmail.com #The superuser email for API
DJANGO_SUPERUSER_PASSWORD=example_password #The superuser password for API

BOT_TOKEN=example_bot_token #Your telegram bot token

UNI_EMAIL_REGEX=^[A-Za-z0-9._%+-]+@aut.ac.ir #A regex for valid emails which can be used for registration
```

### Running the bot

To run the bot simply execute the following command:
```bash
docker-compose up -d --build
```

### Fill the Students Authentication Data and Course Chapters

​	You can use Django admin panel to fill the students authentication data. In order to login to the panel you should go to `localhost:8000/admin` and enter the email and the password for superuser account. 

​	Click the section `Auth Data`. Then you can use `import` button to import students data using a csv,xlsx,json,yaml,... file. The file must contain the fields id, password, email, first_name, last_name and student_id for each student.

Also, you can enter the course chapters in `Categories` section. these chapters are used to sort the resources and to show the timeline of the course which you can edit it in telegram admin panel.

Congratulations! The bot is up and running now :)

# Admins Secret Commands

They are just 2 more commands for admins:

### /register_admin

This command is used to register a chat as admin. The user should send an arbitrary email and then the bot asks for the secret key and if the secret key is entered correctly the chat will have the admin access to the bot.

### /answer

If the admin wants to answer a forwarded question, he/she should reply to that message with /answer command followed by the answer of the question. Ex: `/answer this question is not related to this topic...`

