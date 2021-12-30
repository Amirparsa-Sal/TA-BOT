# TA BOT

This project is an open source telegram bot which can be used as a teaching assistant bot if you are trying to find an easy and secure way to communicate with your students.

# Features

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

  They must send their own email in telegram, then the bot sends a one time password to their email (if they have entered a valid email) and after entering that password, the account is created using the predefined passwords which you have uploaded in admin panel to use them as an authentication mean. 

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

### install Python(>3)

​	You can download and install the last version of the python from [here](https://www.python.org).

### install and Start Redis

​	You can download and install Redis from [here](https://redis.io/download).

### Create a virtual Environment 

​	while you are in the base folder of the project, run this command to create a new virtual environment:

```bash
python3 -m venv env
```

​	You can use any name instead of env.

### Activate the Environment

​	Run the following command to activate the virtual environment:

```bash
source env/bin/activate
```

### Install The Requirements

​	Inside the root folder of the project, run the following command. to install the python required modules:

```bash
pip3 install -r requirements.txt
```

### Create Your Google SMTP Account and Config the Backend

​	You follow this [guide](https://www.hostinger.com/tutorials/how-to-use-free-google-smtp-server) to create your Google SMTP account.

​	Next, go to `API/TA_BOT/TA_BOT` and create a `.env` file:

```bash
touch .env
```

​	You must specify 4 items in that file. The first three items are related to the smtp account and the last one is the secret key which you use to access the admin panel.

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=example@gmail.com
EMAIL_HOST_PASSWORD=example_password
SECRET_KEY=example_secret
```



### Migrate the database

​	Go to `API/TA_BOT` and migrate the database to create a SQLite database:

```bash
python3 manage.py migrate
```

### Create a Superuser

​	Go to `API/TA_BOT` and create a superuser using this command:

```bash
python3 manage.py createsuperuser
```

​	Then you should enter an email and a password for superuser. The bot will use this superuser account to access some restricted APIs. So, remember that email and password because we need to set them in another .env file.

### Config the Telegram Bot

​	Go to `TelegramBot` folder and create another `.env` file:

```bash
touch .env
```

​	You should specify 4 things in this file. Firstly, you should enter the bot token which you have generated using the BotFather. After that you should specify the email and password you used to create the superuser account, and finally there is an optional field which you can specify your own academic email regex to validate users. If you dont specify the regex, the default regex is for Amirkabir University Of Technology(****@aut.ac.ir)

```
BOT_TOKEN=example_token

BOT_API_EMAIL=the_email_you_used_to_create_superuser_account
BOT_API_PASSWORD=the_password_you_used_to_create_superuser_account

UNI_EMAIL_REGEX=^[A-Za-z0-9._%+-]+@aut.ac.ir
```

### Run the Django Server

​	Go to `API/TA_BOT` and run the following command:

```
python3 manage.py runserver 8000
```

​	You can use your arbitrary port numbe(instead of 8000) to deploy the backend server.

### Fill the Students Authentication Data and Course Chapters

​	You can use Django admin panel to fill the students authentication data. In order login to the panel you should go to `localhost:8000/admin` and enter the email and the password for superuser account. 

​	Click the section `Auth Data`. Then you can use `import` button to import students data using a csv,xlsx,json,yaml,... file. The file must contain the fields id, password, email, first_name, last_name and student_id for each student.

Also, you can enter the course chapters in `Categories` section. these chapters are used to sort the resources and to show the timeline of the course which you can edit it in telegram admin panel.

### Run the Telegram Bot

​	Finally, go to `TelegramBot` folder and run the following command:

```bash
python3 bot.py
```



Congratulations! The bot is up and running now :)