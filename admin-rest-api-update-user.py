import requests, json, datetime
from KCAuth import KCAuth

# https://www.keycloak.org/docs/4.1/server_development/index.html#admin-rest-api
# https://www.keycloak.org/docs-api/4.1/rest-api/

REST_API_USERS = "/{realm}/users"
REST_API_USER = "/{realm}/users/{id}"

def getResource(resourceUrl, parameters, token):
    headers = { 'authorization': "Bearer " + token, 'content-type': "application/json" }
    r = requests.get(resourceUrl, headers=headers, params=parameters)
    print("HTTP GET: " + resourceUrl + "\tPARAMETERS: " + str(parameters))
    return r.json()


def updateResource(resourceUrl, data, token):
    headers = { 'authorization': "Bearer " + token, 'content-type': "application/json" }
    r = requests.put(resourceUrl, headers=headers, data=json.dumps(data))
    print("HTTP PUT (Update): " + resourceUrl + "\tDATA: " + json.dumps(data))
    if (r.status_code != 204):
        print("Should receive an HTTP 204 (no content), but something else received...")
        print(r.status_code)
        print(r.text)
        print(r)
        return False
    return True
        
def buildResourceUrl(baseUrl, relativeUrl, urlParams):
    url = baseUrl + relativeUrl
    for key in urlParams:
        param = urlParams[key]
        url = url.replace("{" + key + "}", param)
    return url

if __name__ == '__main__':
    kcAuth = KCAuth("keycloak.master.json")
    adminAccessToken = kcAuth.getAccessToken()
    authServerUrl = kcAuth.getAuthServerUrl()
    resourceBaseUrl = authServerUrl + '/admin/realms'
    resourceRealm =  'SIB-AAI'

    searchUsersResourceUrl = buildResourceUrl(resourceBaseUrl, REST_API_USERS, {"realm" : resourceRealm})
    foundUsers = getResource(searchUsersResourceUrl, {'username':'dummy'}, adminAccessToken)
    userId = foundUsers[0]["id"]
    userResourceUrl = buildResourceUrl(resourceBaseUrl, REST_API_USER, {"realm" : resourceRealm, "id": userId})
    user = getResource(userResourceUrl, {}, adminAccessToken)
    print("Dummy user:")
    print("current attribute " + str(user["attributes"]["test-attribute"]))
    print("current federated identity" + str(user["federatedIdentities"]))

    #This works! (It updates the user with the new / current test-attribute)
    user["firstName"] = "Super Dummy updated at " + str(datetime.datetime.now()) 
    #This works! (It updates the user with the new / current test-attribute)
    user["attributes"]["test-attribute"] = "test attribute updated at " + str(datetime.datetime.now())

    #This does not work! (It should create the federated identity for a give IdP)
    federatedIdentity = user["federatedIdentities"][0]
    federatedIdentity["userName"] = "dummy@uni.edu"
    federatedIdentity["userId"] = "dummy@uni.edu"
    
    #Updates user
    print("Updating user ... ")
    updateResource(userResourceUrl, user, adminAccessToken)

    print("New attribute " + str(user["attributes"]["test-attribute"]))
    print("New federated identity" + str(user["federatedIdentities"]))
    user = getResource(userResourceUrl, {}, adminAccessToken)

    #See that attribute was update but federated identity was not updated...
    print("Check new attribute " + str(user["attributes"]["test-attribute"]))
    print("Check federated identity" + str(user["federatedIdentities"]))
    
