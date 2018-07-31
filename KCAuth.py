import time, getpass, requests, os.path, json, sys
#Note that token settings (access token life time or refresh token sessions) can be changed in realm configuration 

class KCAuth:

    #Attemps to reads from the datastore a valid access token, 
    #If the access token is not valid anymore, it uses the refresh token to attempt to get a new one
    #If the refresh token is not valid anymore, the datastore is deleted and the user must re-enter its credential
    def getAccessTokenFromDatastoreOrRefresh(self):
        if (os.path.isfile(self.datastore_filename)):
            with open(self.datastore_filename, 'r') as f:
                datastore = json.load(f)
                expirationTime = int(datastore["expiration_time"])
                #If the current time is at least 10 seconds above the expiration, return the current access token
                if(expirationTime > int(time.time() + 10)):
                    print("Re-use access token found in datastore " + self.datastore_filename + ", valid till " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expirationTime)) + " (" + str(expirationTime) + ")" )
                    return datastore["access_token"]
                else:
                    return self.requestAccessTokenBasedOnRefreshToken(datastore)
        else:
            return None

    #Gets an access token based on the refresh token 
    #If an error occurs the datastore is deleted
    #TODO should be called only if refresh token expiration time is still valid
    def requestAccessTokenBasedOnRefreshToken(self, datastore) : 
        print("Using refresh token to get a new access token (refresh token is valid for " + str(int(datastore["refresh_expires_in"]) / 60) + " minutes)")
        refresh_token = datastore["refresh_token"]
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id
        }

        #Add secret if configured
        if(self.secret):
            payload["client_secret"] = self.secret

        r = requests.post(self.getOrRequestTokenEndPoint(), data=payload)
        if (r.status_code != 200):
            print("Some error occured, http code: " + str(r.status_code))
            print(r.text)
            print("ERROR exiting and deleting " + self.datastore_filename + " file.")
            os.remove(self.datastore_filename)
            print("Try again (the datastore file was deleted) and user credentials will be asked again")
            sys.exit(1)
        else:
            return self.saveTokensAndGetAccessToken(r)

    #Gets an access token based on user credentials (when no datastore found)
    def requestAccessTokenBasedOnUserCredentials(self) : 
        print("No refresh_token found on datastore (" + self.datastore_filename + "), therefore user credentials will be prompted")
        user = raw_input("username:")
        passwd = getpass.getpass("password:")
        payload = {
            "username": user, 
            "password": passwd,
            "grant_type": "password",
            "client_id": self.client_id
        }

        #Add secret if configured
        if(self.secret):
            payload["client_secret"] = self.secret

        r = requests.post(self.getOrRequestTokenEndPoint(), data=payload)
        if (r.status_code != 200):
            print("Some error occured, http code: " + str(r.status_code))
            print(r.text)
            print("ERROR exiting.")
            sys.exit(1)
        else:
            return self.saveTokensAndGetAccessToken(r)


    #Attemps to get an access token, first from the datastore and if not present credentials will be asked 
    def getAccessToken(self):
        accessToken = self.getAccessTokenFromDatastoreOrRefresh()
        if (accessToken == None):
            return self.requestAccessTokenBasedOnUserCredentials()
        return accessToken

    #Utility method to save access and refresh token
    #Additionaly expiration_time is computed, based on the current time and the expires_in field
    def saveTokensAndGetAccessToken(self, response):
        print("Saving tokens information to datastore: " + self.datastore_filename)
        tokens = response.json()
        accessToken = tokens["access_token"]
        if(not hasattr(tokens, "expiration_time")):
            tokens["expiration_time"] = (int(time.time()) + int(tokens["expires_in"]))
        with open(self.datastore_filename, 'w') as outfile:
            json.dump(tokens, outfile)
        return accessToken

    #Request Keycloak for the 'token_endpoint' at the .well-known configuration
    def getOrRequestTokenEndPoint(self):
        #Assign it only once if needed
        if(len(self.token_endpoint) < 10):
            print ("Asking well known configuration about token endpoint (to retrieve access tokens)")
            r = requests.get(self.keycloak_realm_url + '.well-known/openid-configuration')
            print("Requesting: " + self.keycloak_realm_url + '.well-known/openid-configuration')
            token_endpoint = r.json()["token_endpoint"]
            print("Token endpoint: " + token_endpoint)
            self.token_endpoint = token_endpoint
        
        return self.token_endpoint

    
    def __init__(self, configKcFile):
        with open(configKcFile) as f:
            data = json.load(f)

        self.datastore_filename = ".kc." + configKcFile.replace(".json", ".tokens")
        self.auth_server_url = data["auth-server-url"]
        if(self.auth_server_url.endswith("/")):
            print("!!!!!!!! auth-server-url should not end with '/', this script will likely fail !!!!!!!!!")
        self.realm = data["realm"]
        self.keycloak_realm_url = self.auth_server_url + "/realms/" + self.realm + "/"
        self.client_id = data["resource"]
        self.secret = data["credentials"]["secret"]
        self.token_endpoint = ""

if __name__ == '__main__':
    if(len(sys.argv) == 2):
        print("Using configuration file " + sys.argv[1])
        kcauth = KCAuth(sys.argv[1])
    else:
        defaultKeycloakFile = "keycloak.json"
        print("Keycloak configuration not passed as argument, taking default file name: " + defaultKeycloakFile)
        kcauth = KCAuth("keycloak.json")

    accessToken = kcauth.getAccessToken()
    print("\nYour access token:")
    print(accessToken)