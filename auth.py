import time, getpass, requests, os.path, json, sys
#Note that token settings (access token life time or refresh token sessions) can be changed in realm configuration 

#File to store tokens information 
datastore_filename = 'tokens.json'

# Configuration (REPLACE WITH YOUR SETTINGS)
keycloak_realm_url = 'https://<KEYCLOAK-HOST>/auth/realms/<REALM-NAME>/'
client_id = '<CLIENT-ID>'
client_secret = '<CLIENT-SECRET>'

#Request Keycloak for the 'token endpoint', this method is optional because, the endpoint is generally well known
def requestTokenEndPoint():
    print ("Asking well known configuration about token endpoint (to retrieve access tokens)")
    r = requests.get(keycloak_realm_url + '.well-known/openid-configuration')
    print("Requesting: " + keycloak_realm_url + '.well-known/openid-configuration')
    token_endpoint = r.json()["token_endpoint"]
    print("Token endpoint: " + token_endpoint)
    return token_endpoint

#This method could be used to read the endpoint (but to avoid uncessary calls for a static token endpoint, we assign directly keycloak_realm_url by appending suffix: 'protocol/openid-connect/token'
#token_endpoint = requestTokenEndPoint()
token_endpoint = keycloak_realm_url + 'protocol/openid-connect/token'

#Attemps to reads from the datastore a valid access token, 
#If the access token is not valid anymore, it uses the refresh token to attempt to get a new one
#If the refresh token is not valid anymore, the datastore is deleted and the user must re-enter its credential
def getAccessTokenFromDatastoreOrRefresh():
    if (os.path.isfile(datastore_filename)):
        with open(datastore_filename, 'r') as f:
            datastore = json.load(f)
            expirationTime = int(datastore["expiration_time"])
            #If the current time is at least 10 seconds above the expiration, return the current access token
            if(expirationTime > int(time.time() + 10)):
                print("Re-use access token found in datastore " + datastore_filename + ", valid till " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expirationTime)) + " (" + str(expirationTime) + ")" )
                return datastore["access_token"]
            else:
                return requestAccessTokenBasedOnRefreshToken(datastore)
    else:
        return None

#Gets an access token based on the refresh token 
#If an error occurs the datastore is deleted
#TODO should be called only if refresh token expiration time is still valid
def requestAccessTokenBasedOnRefreshToken(datastore) : 
    print("Using refresh token to get a new access token (refresh token is valid for " + str(int(datastore["refresh_expires_in"]) / 60) + " minutes)")
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
        print("Try again (the datastore file was deleted) and user credentials will be asked again")
        sys.exit(1)
    else:
        return saveTokensAndGetAccessToken(r)

#Gets an access token based on user credentials (when no datastore found)
def requestAccessTokenBasedOnUserCredentials() : 
    print("No refresh_token found on datastore (" + datastore_filename + "), therefore user credentials will be prompted")
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


#Attemps to get an access token, first from the datastore and if not present credentials will be asked 
def getValidAccessToken() : 
    accessToken = getAccessTokenFromDatastoreOrRefresh()
    if (accessToken == None) :
        return requestAccessTokenBasedOnUserCredentials()
    return accessToken

#Utility method to save access and refresh token
#Additionaly expiration_time is computed, based on the current time and the expires_in field
def saveTokensAndGetAccessToken(response):
    print("Saving tokens information to datastore: " + datastore_filename)
    tokens = response.json()
    accessToken = tokens["access_token"]
    if(not hasattr(tokens, "expiration_time")):
        tokens["expiration_time"] = (int(time.time()) + int(tokens["expires_in"]))
    with open(datastore_filename, 'w') as outfile:
        json.dump(tokens, outfile)
    return accessToken

if __name__ == '__main__':
    accessToken = getValidAccessToken()
    print("\nYour access token:")
    print(accessToken)
