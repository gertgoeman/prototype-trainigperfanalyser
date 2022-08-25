# prototype-trainingperfanalyser

## Setting up the environment

Note: currently works with python 3.10

Create a new virtual environment named 'env':

    python3.10 -m venv env

Activate the enviromnent:

    source env/bin/activate

## Getting an access token

1. Go to url:

http://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read_all,activity:read_all

And replace {client_id} with id from strava

2. The redirect_url has a "code" in the querystring. Exchange it for an access_token:

curl -X POST https://www.strava.com/oauth/token \
-F client_id={client_id} \
-F client_secret={client_secret} \
-F code={code} \
-F grant_type=authorization_code

And again, replace client_id, client_secret and code with the correct values.
