import time
import getpass, requests
import os.path
import json, sys

keycloak_realm_url = 'https://<KEYCLOAK-HOST>/auth/realms/<REALM-NAME>/'
client_id = '<CLIENT-ID>'
client_secret = '<CLIENT-SECRET>'
token_endpoint = keycloak_realm_url + 'protocol/openid-connect/token'

datastore_filename = 'tokens.json'

#Token settings (access token life time or refresh token sessions) can be changed in realm configuration 

#This method could be used to read the endpoint (but it is must faster to assign directly the correct sufix to the keycloak_realm_url...
def readTokenEndPoint():
    print ("Asking well known configuration about token endpoint (to retrieve access tokens)")
    r = requests.get(oidc_url + '.well-known/openid-configuration')
    print("Requesting: " + oidc_url + '.well-known/openid-configuration')
    token_endpoint = r.json()["token_endpoint"]
    print("Token endpoint: " + token_endpoint)
    return token_endpoint

#token_endpoint = readTokenEndPoint()

def readAccessToken():
    if (os.path.isfile(datastore_filename)):
        with open(datastore_filename, 'r') as f:
            datastore = json.load(f)
            expirationTime = int(datastore["expiration_time"])
            #If the current time is at least 10 seconds above the expiration, return the access token
            if(expirationTime > int(time.time() + 10)):
                print("Re-use access token found in datastore file " + datastore_filename + ", valid till " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expirationTime)) + " (" + str(expirationTime) + ")" )
                return datastore["access_token"]

            print("Using refresh token to get a new access token (refresh token is valid for " + str(int(datastore["refresh_expires_in"]) / 60) + " minutes)")
            #TODO should read access_token and check if it is expired already, instead of asking everytime 
            refresh_token = datastore["refresh_token"]
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret
            }
            r = requests.post(token_endpoint, data=payload)
            if (r.status_code != 200):
                print("Some error occured")
                print(r.text)
                print("ERROR exiting and deleting " + datastore_filename + " file.")
                os.remove(datastore_filename)
                print("Try again (the datastore file is deleted) and user credentials will be asked again")
                sys.exit(1)
            else:
                return saveTokensAndGetAccessToken(r)
    else:
        return None

def saveTokensAndGetAccessToken(response):
    tokens = response.json()
    accessToken = tokens["access_token"]
    os.environ["INSIGHTS_TOKEN"] = accessToken
    if(not hasattr(tokens, "expiration_time")):
        tokens["expiration_time"] = (int(time.time()) + int(tokens["expires_in"]))
    with open(datastore_filename, 'w') as outfile:
        json.dump(tokens, outfile)
    return accessToken

def getAccessToken() : 
    accessToken = readAccessToken()
    if (accessToken == None) :
        print("No refresh_token found on datastore (" + datastore_filename + "), therefore user credentials are required")
        user = raw_input("username:")
        passwd = getpass.getpass("password:")
        payload = {
            "username": user, 
            "password": passwd,
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret
        }
        r = requests.post(token_endpoint, data=payload)
        if (r.status_code != 200):
            print("Some error occured")
            print(r.text)
            print("ERROR exiting.")
            sys.exit(1)
        else:
            return saveTokensAndGetAccessToken(r)
    return accessToken

if __name__ == '__main__':
    accessToken = getAccessToken()
    print "\nYour access token:"
    print accessToken
