# cyclosbot
telegram bot that connect to cyclos platform

# Current features
1. Register users 
2. Check balance of registered users
3. Post anounces
4. Report problems to admin
5. All commands can be sended using predefined buttons

# Install
Requirements: python 3.6, pip, django, postgres

First we need to install postgres if we dont have it installed yet

Debian/ubuntu:
apt-get install postgresql

Then download the source where yo prefer

git clone git clone https://github.com/Daklon/cyclosbot-django.git

Also you can install virtualenv or similar but its out of the scope of this readme

Now you must install the requirements

pip install -r requirements.txt

After that you have to configure django, go to cyclosbot/cyclosbot/settings.py
Edit the secret key (generate a new one), and edit the database config to connect django to your database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'djangobot',
        'USER': 'bot',
        'PASSWORD': 'astrongpasswordormaybenot',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

Create the users and database if you didnt have one
http://www.sakana.fr/blog/2007/06/06/postgresql-create-a-user-a-database-and-grant-accesses/

Now, in the root of django, you should fiil the databe
python manage.py migrate

Finally, go to the telegrambot dir, in the root of the project and edit config.py

If you like you can run main.py using supervisor, also you can simply run python main.py

# TODO
1. Post anounces 
	2. improve category management
2. Make payments
3. Add funtion to list anounces
4. Search anounces
5. Improve installation
6. Improve documentation
